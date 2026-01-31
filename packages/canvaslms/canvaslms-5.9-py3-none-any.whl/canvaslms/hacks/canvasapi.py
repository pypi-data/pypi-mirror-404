"""A module that modifies the classes of the canvasapi package"""

import cachetools
import canvasapi.assignment
from canvasapi.user import User
from datetime import datetime, timedelta
import functools
import importlib
import inspect
import logging
import time
import sys

logger = logging.getLogger(__name__)

NOREFRESH_GRADES = ["A", "P", "P+", "complete"]
# Cache TTL constants
SUBMISSION_TTL_MINUTES = 5
DEFAULT_CACHE_TTL_DAYS = 7
USER_CACHE_TTL_DAYS = 2
GROUP_CACHE_TTL_DAYS = 5
QUIZ_CACHE_TTL_DAYS = 3
THRESHOLD_INDIVIDUAL_REFRESH = 6


def make_classes_comparable():
    """Improves the classes by adding __eq__ and __hash__ methods"""

    def canvas_comparable(cls):
        def is_equal(self, other):
            """Tests if Canvas objects self and other refer to the same object"""
            return type(self) == type(other) and self.id == other.id

        cls.__eq__ = is_equal
        return cls

    def canvas_hashable(cls):
        def canvas_hash(self):
            """Returns a hash suitable for Canvas objects"""
            return hash(type(self)) ^ hash(self.id)

        cls.__hash__ = canvas_hash
        return cls

    # classes to improve in each module
    CANVASAPI_CLASSES = {
        "assignment": ["Assignment", "AssignmentGroup"],
        "submission": ["Submission"],
        "user": ["User"],
        "group": ["GroupCategory", "Group"],
        "module": ["Module"],
    }
    canvasapi_modules = {}

    # import all modules
    for module_name in CANVASAPI_CLASSES:
        canvasapi_modules[module_name] = importlib.import_module(
            f"canvasapi.{module_name}"
        )
    for module_name, module in canvasapi_modules.items():
        module_members = inspect.getmembers(module)
        for obj_name, obj in module_members:
            if obj_name in CANVASAPI_CLASSES[module_name]:
                canvas_comparable(obj)
                canvas_hashable(obj)


def make_useful_user_dunder_str():
    """Improves the user class by changing __str__"""

    def name_and_login(self):
        try:
            return f"{self.name} <{self.login_id}>"
        except AttributeError as err:
            return f"{self.name} <>"

    import canvasapi.user

    canvasapi.user.User.__str__ = name_and_login


def must_update(prev_kwargs, new_kwargs, ignore_keys=["sort", "order", "order_by"]):
    """
    Returns True if we must update the cache (refetch).

    By default, we ignore the keys

      "sort",
      "order",
      "order_by"

    as they don't affect the caching.
    """
    for key, value in new_kwargs.items():
        # Skip ignored keys (like sorting parameters)
        if key in ignore_keys:
            continue

        if key not in prev_kwargs:
            return True
        elif isinstance(value, list):
            if set(value) > set(prev_kwargs[key]):
                return True
        elif value != prev_kwargs[key]:
            return True

    return False


def merge_kwargs(kwargs_list, ignore_keys=["sort", "order", "order_by"]):
    """
    Merges a list of keyword arguments dictionaries. Lists are unioned.
    All non-list keys (usually strings) must be the same in all dictionaries.

    By default, we ignore the keys

      "sort",
      "order",
      "order_by"

    as they don't affect the caching.
    """
    new_kwargs = dict()

    for kwargs in kwargs_list:
        for key, value in kwargs.items():
            if key not in new_kwargs:
                new_kwargs[key] = value
            elif isinstance(value, list) or isinstance(new_kwargs[key], list):
                # Convert both to lists if either is a list, then union
                prev_val = (
                    new_kwargs[key]
                    if isinstance(new_kwargs[key], list)
                    else [new_kwargs[key]]
                )
                curr_val = value if isinstance(value, list) else [value]
                new_kwargs[key] = list(set(prev_val) | set(curr_val))
            else:
                if key in ignore_keys:
                    new_kwargs[key] = value
                elif value != new_kwargs[key]:
                    raise ValueError(
                        f"Cannot merge {key} with " f"{value} and {new_kwargs[key]}"
                    )

    return new_kwargs


class CacheGetMethods:
    """
    General class decorator to add caching to get_*{,s} methods.

    We assume that the first positional argument identifies the object to fetch.
    By default, this must match the [[.id]] attribute of the returned object.
    For objects identified by other attributes (e.g., pages use URL slugs), use
    the [[cache_key]] parameter to specify which attribute to use.

    Parameters:
      attribute_name: The attribute name to cache (e.g., "assignment", "user").
      cache: Optional initial cache dictionary (default: {}).
      include_plural: Whether to cache the plural method get_*s (default: True).
      include_singular: Whether to cache the singular method get_* (default: True).
      plural_name: Custom plural name for irregular plurals (default: None, uses
                   attribute_name + "s"). For example, "group_categories" instead
                   of "group_categorys".
      cache_key: The attribute name to use as cache key (default: 'id'). For
                 objects identified by URL instead of numeric ID (like pages),
                 use cache_key='url'.
    """

    def __init__(
        self,
        attribute_name,
        cache=None,
        include_plural=True,
        include_singular=True,
        plural_name=None,
        cache_key="id",
    ):
        """No parameters required"""
        self.__attribute_name = attribute_name
        self.__include_plural = include_plural
        self.__include_singular = include_singular
        self.__plural_name = plural_name
        self.__cache = cache if cache else {}
        self.__cache_key = cache_key

    def __call__(self, cls):
        """Applies the decorator to the class cls"""
        init = cls.__init__
        attr_name = self.__attribute_name
        cache_key = self.__cache_key

        @functools.wraps(init)
        def new_init(*args, **kwargs):
            self = args[0]
            if not hasattr(self, f"{attr_name}_cache"):
                setattr(self, f"{attr_name}_cache", {})
            if not hasattr(self, f"{attr_name}_all_fetched"):
                setattr(self, f"{attr_name}_all_fetched", None)
            init(*args, **kwargs)

        cls.__init__ = new_init

        if self.__include_singular:
            singular_name = f"get_{self.__attribute_name}"
            get_attr = getattr(cls, singular_name)
            cache_key = self.__cache_key

            @functools.wraps(get_attr)
            def new_get_attr(self, *args, **kwargs):
                attr_cache = getattr(self, f"{attr_name}_cache")

                try:
                    arg = args[0]
                    id = getattr(arg, cache_key)
                except IndexError:
                    raise TypeError(
                        f"{singular_name}() missing 1 required positional "
                        f"argument: '{cache_key}'"
                    )
                except AttributeError:
                    # Stricter type checking based on cache_key
                    if cache_key == "id":
                        # ID-based caching: only accept integers
                        if isinstance(arg, int):
                            id = arg
                        else:
                            raise TypeError(
                                f"{singular_name}() argument 1 must be int or "
                                f"Canvas object with id, not {type(arg).__name__}"
                            )
                    else:
                        # URL or other string-based caching: accept int or str
                        if isinstance(arg, (int, str)):
                            id = arg
                        else:
                            raise TypeError(
                                f"{singular_name}() argument 1 must be int, str, or "
                                f"Canvas object, not {type(arg).__name__}"
                            )

                try:
                    obj, prev_kwargs = attr_cache[id]
                    cache_status = ""
                except KeyError:
                    obj = None
                    prev_kwargs = {}
                    cache_status = " (not found)"

                if obj and must_update(prev_kwargs, kwargs):
                    obj = None
                    cache_status = " (new kwargs required)"
                elif obj and outdated(obj):
                    reason = get_staleness_reason(obj)
                    obj = None
                    cache_status = f" (stale: {reason})" if reason else " (stale)"

                if not obj:
                    fetch_start = time.perf_counter()
                    obj = get_attr(self, *args, **kwargs)
                    fetch_elapsed = time.perf_counter() - fetch_start
                    obj._fetched_at = datetime.now()
                    attr_cache[getattr(obj, cache_key)] = (obj, kwargs)
                    logger.info(
                        f"Cache miss{cache_status}: {attr_name} {cache_key}={id} fetched in "
                        f"{fetch_elapsed:.2f}s"
                    )
                else:
                    logger.info(f"Cache hit: {attr_name} {cache_key}={id}")

                return obj

            setattr(cls, singular_name, new_get_attr)

        if self.__include_plural:
            if self.__plural_name:
                plural_name = f"get_{self.__plural_name}"
                display_plural = self.__plural_name
            else:
                plural_name = f"get_{self.__attribute_name}s"
                display_plural = f"{self.__attribute_name}s"
            get_attrs = getattr(cls, plural_name)
            cache_key = self.__cache_key

            @functools.wraps(get_attrs)
            def new_get_attrs(self, *args, **kwargs):
                attr_cache = getattr(self, f"{attr_name}_cache")
                attr_all_fetched = getattr(self, f"{attr_name}_all_fetched")

                if attr_all_fetched:
                    for _, prev_kwargs in attr_cache.values():
                        if must_update(prev_kwargs, kwargs):
                            logger.info(
                                f"Cache invalidation: {display_plural} - new kwargs required "
                                f"(existing: {prev_kwargs}, requested: {kwargs})"
                            )
                            attr_all_fetched = None
                            break

                if not attr_all_fetched:
                    if not attr_cache:
                        refresh_reason = "first fetch (cold cache)"
                    else:
                        refresh_reason = "cache invalidated"
                    logger.info(f"Bulk fetch: {display_plural} - {refresh_reason}")
                    bulk_start = time.perf_counter()

                    original_includes = set(kwargs.get("include", []))
                    union_kwargs = merge_kwargs(
                        [kwargs for _, kwargs in attr_cache.values()] + [kwargs]
                    )
                    merged_includes = set(union_kwargs.get("include", []))

                    if merged_includes != original_includes:
                        added = merged_includes - original_includes
                        logger.info(
                            f"Merging kwargs for {attr_name}: extending include fields "
                            f"from {sorted(original_includes)} to {sorted(merged_includes)} "
                            f"(added: {sorted(added)})"
                        )

                    api_start = time.perf_counter()
                    fetched_objs = list(get_attrs(self, *args, **union_kwargs))
                    api_elapsed = time.perf_counter() - api_start

                    process_start = time.perf_counter()
                    for obj in fetched_objs:
                        obj_key = getattr(obj, cache_key)
                        old_entry = attr_cache.get(obj_key, None)
                        if old_entry:
                            old_obj, _ = old_entry
                            for cache_attr_name in dir(old_obj):
                                if cache_attr_name.endswith(
                                    "_cache"
                                ) or cache_attr_name.endswith("_all_fetched"):
                                    setattr(
                                        obj,
                                        cache_attr_name,
                                        getattr(old_obj, cache_attr_name),
                                    )
                        obj._fetched_at = datetime.now()
                        attr_cache[obj_key] = (obj, union_kwargs)
                    process_elapsed = time.perf_counter() - process_start

                    setattr(self, f"{attr_name}_all_fetched", datetime.now())
                    attr_all_fetched = getattr(self, f"{attr_name}_all_fetched")

                    bulk_elapsed = time.perf_counter() - bulk_start
                    logger.info(
                        f"Bulk refresh completed: {len(fetched_objs)} {display_plural} fetched in "
                        f"{bulk_elapsed:.2f}s (API: {api_elapsed:.2f}s, "
                        f"processing: {process_elapsed:.2f}s)"
                    )
                    for obj, _ in attr_cache.values():
                        yield obj
                else:
                    cache_age = datetime.now() - attr_all_fetched
                    stale_count = sum(
                        1 for obj, _ in attr_cache.values() if outdated(obj)
                    )
                    logger.info(
                        f"Using cached {display_plural}: {len(attr_cache)} cached "
                        f"(age: {cache_age.total_seconds()/60:.1f} minutes, "
                        f"{stale_count} stale), updating stale entries individually"
                    )
                    for obj, obj_kwargs in attr_cache.values():
                        if outdated(obj):
                            obj_key = getattr(obj, cache_key)
                            reason = get_staleness_reason(obj)
                            reason_str = f" (reason: {reason})" if reason else ""
                            refresh_start = time.perf_counter()
                            obj = get_attr(self, obj_key, **obj_kwargs)
                            refresh_elapsed = time.perf_counter() - refresh_start
                            logger.info(
                                f"Individual refresh: {attr_name} {cache_key}={obj_key} in "
                                f"{refresh_elapsed:.2f}s{reason_str}"
                            )
                            obj._fetched_at = datetime.now()
                            attr_cache[obj_key] = (obj, obj_kwargs)
                        yield obj

            setattr(cls, plural_name, new_get_attrs)
        return cls


def outdated(obj):
    """Returns True if the object obj is outdated"""
    try:
        if obj.grade not in NOREFRESH_GRADES:
            try:
                if datetime.now() - obj._fetched_at > timedelta(
                    minutes=SUBMISSION_TTL_MINUTES
                ):
                    return True
            except AttributeError:
                return True
    except AttributeError:
        pass
    try:
        # If obj has page_id, it's a Page object
        page_id = obj.page_id
        # Page objects from get_pages() lack body; treat as incomplete
        if not hasattr(obj, "body") or obj.body is None:
            return True
    except AttributeError:
        pass
    for attr_name in dir(obj):
        if attr_name == "user_all_fetched":
            if not getattr(obj, attr_name):
                continue
            elif datetime.now() - getattr(obj, attr_name) > timedelta(
                days=USER_CACHE_TTL_DAYS
            ):
                age = datetime.now() - getattr(obj, attr_name)
                logger.info(
                    f"Cache invalidation: user_all_fetched periodic refresh "
                    f"(age: {age.days} days, threshold: {USER_CACHE_TTL_DAYS} days)"
                )
                setattr(obj, attr_name, None)
        elif attr_name in ["group_all_fetched", "group_category_all_fetched"]:
            if not getattr(obj, attr_name):
                continue
            elif datetime.now() - getattr(obj, attr_name) > timedelta(
                days=GROUP_CACHE_TTL_DAYS
            ):
                age = datetime.now() - getattr(obj, attr_name)
                logger.info(
                    f"Cache invalidation: {attr_name} periodic refresh "
                    f"(age: {age.days} days, threshold: {GROUP_CACHE_TTL_DAYS} days)"
                )
                setattr(obj, attr_name, None)
        elif attr_name in ["quiz_all_fetched", "new_quiz_all_fetched"]:
            if not getattr(obj, attr_name):
                continue
            elif datetime.now() - getattr(obj, attr_name) > timedelta(
                days=QUIZ_CACHE_TTL_DAYS
            ):
                age = datetime.now() - getattr(obj, attr_name)
                logger.info(
                    f"Cache invalidation: {attr_name} periodic refresh "
                    f"(age: {age.days} days, threshold: {QUIZ_CACHE_TTL_DAYS} days)"
                )
                setattr(obj, attr_name, None)
        elif attr_name.endswith("_all_fetched"):
            if not getattr(obj, attr_name):
                continue
            elif datetime.now() - getattr(obj, attr_name) > timedelta(
                days=DEFAULT_CACHE_TTL_DAYS
            ):
                age = datetime.now() - getattr(obj, attr_name)
                logger.info(
                    f"Cache invalidation: {attr_name} periodic refresh "
                    f"(age: {age.days} days, threshold: {DEFAULT_CACHE_TTL_DAYS} days)"
                )
                setattr(obj, attr_name, None)
    return False


def get_staleness_reason(obj):
    """
    Returns a descriptive string explaining why obj is stale, or None if fresh.
    Mirrors the logic in outdated() but returns human-readable reasons.
    Uses constants for TTL values to ensure consistency with outdated() logic.
    """
    try:
        page_id = obj.page_id
        if not hasattr(obj, "body") or obj.body is None:
            return "incomplete page object (missing body from get_pages())"
    except AttributeError:
        pass
    try:
        if obj.grade not in NOREFRESH_GRADES:
            try:
                age = datetime.now() - obj._fetched_at
                ttl = timedelta(minutes=SUBMISSION_TTL_MINUTES)
                if age > ttl:
                    expired_by = age - ttl
                    return (
                        f"non-passing grade ({obj.grade}), "
                        f"{SUBMISSION_TTL_MINUTES}-minute TTL expired "
                        f"{expired_by.total_seconds()/60:.1f} minutes ago"
                    )
            except AttributeError:
                return "non-passing grade, missing _fetched_at attribute"
    except AttributeError:
        pass
    for attr_name in dir(obj):
        if attr_name == "user_all_fetched":
            attr_val = getattr(obj, attr_name, None)
            if attr_val:
                age = datetime.now() - attr_val
                threshold = timedelta(days=USER_CACHE_TTL_DAYS)
                if age > threshold:
                    return (
                        f"periodic refresh: {attr_name} "
                        f"(age: {age.days} days, threshold: {USER_CACHE_TTL_DAYS} days)"
                    )
        elif attr_name in ["group_all_fetched", "group_category_all_fetched"]:
            attr_val = getattr(obj, attr_name, None)
            if attr_val:
                age = datetime.now() - attr_val
                threshold = timedelta(days=GROUP_CACHE_TTL_DAYS)
                if age > threshold:
                    return (
                        f"periodic refresh: {attr_name} "
                        f"(age: {age.days} days, threshold: {GROUP_CACHE_TTL_DAYS} days)"
                    )
        elif attr_name in ["quiz_all_fetched", "new_quiz_all_fetched"]:
            attr_val = getattr(obj, attr_name, None)
            if attr_val:
                age = datetime.now() - attr_val
                threshold = timedelta(days=QUIZ_CACHE_TTL_DAYS)
                if age > threshold:
                    return (
                        f"periodic refresh: {attr_name} "
                        f"(age: {age.days} days, threshold: {QUIZ_CACHE_TTL_DAYS} days)"
                    )
        elif attr_name.endswith("_all_fetched"):
            attr_val = getattr(obj, attr_name, None)
            if attr_val:
                age = datetime.now() - attr_val
                threshold = timedelta(days=DEFAULT_CACHE_TTL_DAYS)
                if age > threshold:
                    return (
                        f"periodic refresh: {attr_name} "
                        f"(age: {age.days} days, threshold: {DEFAULT_CACHE_TTL_DAYS} days)"
                    )
    return None


def make_canvas_courses_cacheable():
    import canvasapi.canvas

    canvasapi.canvas.Canvas = CacheGetMethods("course")(canvasapi.canvas.Canvas)


def make_course_contents_cacheable():
    import canvasapi.course

    canvasapi.course.Course = CacheGetMethods("assignment")(canvasapi.course.Course)
    canvasapi.course.Course = CacheGetMethods("user")(canvasapi.course.Course)


def make_course_pages_cacheable():
    import canvasapi.course

    canvasapi.course.Course = CacheGetMethods("page", cache_key="url")(
        canvasapi.course.Course
    )


def make_course_assignment_groups_cacheable():
    import canvasapi.course

    canvasapi.course.Course = CacheGetMethods("assignment_group")(
        canvasapi.course.Course
    )


def make_course_modules_cacheable():
    import canvasapi.course

    canvasapi.course.Course = CacheGetMethods("module")(canvasapi.course.Course)


def make_module_items_cacheable():
    import canvasapi.module

    canvasapi.module.Module = CacheGetMethods("module_item")(canvasapi.module.Module)


def make_module_item_resolvable():
    """Add resolution methods to ModuleItem for accessing cached content objects."""
    import canvasapi.module

    def resolve_to_page(self, course):
        """Resolve this Page module item to a cached Page object.

        Args:
            course: The Course object containing this module

        Returns:
            Page: The cached Page object

        Raises:
            TypeError: If this is not a Page item
        """
        if not hasattr(self, "type") or self.type != "Page":
            raise TypeError(
                f"Cannot resolve {getattr(self, 'type', 'Unknown')} " f"item to Page"
            )
        page = course.get_page(self.page_url)
        page.course = course
        return page

    def resolve_to_assignment(self, course):
        """Resolve this Assignment module item to a cached Assignment object.

        Args:
            course: The Course object containing this module

        Returns:
            Assignment: The cached Assignment object

        Raises:
            TypeError: If this is not an Assignment item
        """
        if not hasattr(self, "type") or self.type != "Assignment":
            raise TypeError(
                f"Cannot resolve {getattr(self, 'type', 'Unknown')} "
                f"item to Assignment"
            )
        assignment = course.get_assignment(self.content_id)
        assignment.course = course
        return assignment

    def resolve(self, course):
        """Resolve this module item to its cached content object.

        Args:
            course: The Course object containing this module

        Returns:
            The cached Page or Assignment object, or None for unsupported types
            (File, ExternalUrl, SubHeader, etc.)
        """
        item_type = getattr(self, "type", None)
        if item_type == "Page":
            return self.resolve_to_page(course)
        elif item_type == "Assignment":
            return self.resolve_to_assignment(course)
        return None

    canvasapi.module.ModuleItem.resolve_to_page = resolve_to_page
    canvasapi.module.ModuleItem.resolve_to_assignment = resolve_to_assignment
    canvasapi.module.ModuleItem.resolve = resolve


def make_course_groups_cacheable():
    import canvasapi.course
    import canvasapi.group

    canvasapi.course.Course = CacheGetMethods(
        "group_category", include_singular=False, plural_name="group_categories"
    )(canvasapi.course.Course)
    canvasapi.course.Course = CacheGetMethods("group", include_singular=False)(
        canvasapi.course.Course
    )
    canvasapi.group.GroupCategory = CacheGetMethods("group", include_singular=False)(
        canvasapi.group.GroupCategory
    )


def make_course_quizzes_cacheable():
    """Add caching to Course.get_quiz/get_quizzes and get_new_quiz/get_new_quizzes"""
    import canvasapi.course

    canvasapi.course.Course = CacheGetMethods("quiz", plural_name="quizzes")(
        canvasapi.course.Course
    )
    canvasapi.course.Course = CacheGetMethods("new_quiz", plural_name="new_quizzes")(
        canvasapi.course.Course
    )


def make_assignment_submissions_cacheable():
    def cache_submissions(cls):
        """Class decorator for cacheable get_submission, get_submissions methods"""
        old_constructor = cls.__init__

        @functools.wraps(cls.__init__)
        def new_init(self, *args, **kwargs):
            self.__cache = {}
            self.__all_fetched = None
            old_constructor(self, *args, **kwargs)

        cls.__init__ = new_init

        get_submission = cls.get_submission

        @functools.wraps(cls.get_submission)
        def new_get_submission(self, user, **kwargs):
            # canvasapi allows either User object or user ID.
            if isinstance(user, User):
                uid = user.id
            elif isinstance(user, int):
                uid = user
            else:
                raise TypeError(f"user must be User or int")

            submission = None

            if "include" in kwargs:
                to_include = set(kwargs["include"])
            else:
                to_include = set()

            if must_refresh(uid, to_include, self.__cache):
                fetch_start = time.perf_counter()
                submission = get_submission(self, user, include=list(to_include))
                fetch_elapsed = time.perf_counter() - fetch_start
                submission._fetched_at = datetime.now()
                logger.info(f"Fetched submission user_id={uid} in {fetch_elapsed:.2f}s")
                self.__cache[uid] = (submission, to_include)
            else:
                submission, _ = self.__cache[uid]

            return submission

        cls.get_submission = new_get_submission

        get_submissions = cls.get_submissions

        @functools.wraps(cls.get_submissions)
        def new_get_submissions(self, *args, **kwargs):
            if "include" in kwargs:
                to_include = set(kwargs["include"])
            else:
                to_include = set()

            # Collect everything to include from before.
            for _, included in self.__cache.values():
                to_include |= included

            if self.__all_fetched:
                cache_age = datetime.now() - self.__all_fetched
                logger.info(
                    f"Using cached submissions for assignment id={self.id}: "
                    f"{len(self.__cache)} submissions cached "
                    f"(age: {cache_age.total_seconds()/60:.1f} minutes), "
                    f"checking staleness to decide refresh strategy"
                )
                num_needs_refresh = 0
                for submission, included in self.__cache.values():
                    if must_refresh(submission.user_id, to_include, self.__cache):
                        num_needs_refresh += 1
                        if num_needs_refresh > THRESHOLD_INDIVIDUAL_REFRESH:
                            break

                if num_needs_refresh <= THRESHOLD_INDIVIDUAL_REFRESH:
                    logger.info(
                        f"Refreshing {num_needs_refresh} individual submissions "
                        f"for assignment id={self.id}"
                    )
                    for submission, _ in self.__cache.values():
                        # Use the cached method above to trigger any individual refreshes.
                        self.get_submission(
                            submission.user_id, include=list(to_include)
                        )
                else:
                    logger.info(
                        f"Refreshing all submissions for assignment id={self.id} "
                        f"due to {num_needs_refresh} needing refresh"
                    )
                    start_fetch = time.perf_counter()
                    submissions = list(get_submissions(self, include=list(to_include)))
                    fetch_elapsed = time.perf_counter() - start_fetch
                    logger.info(
                        f"Bulk refresh: {len(submissions)} submissions in "
                        f"{fetch_elapsed:.2f}s"
                    )

                    for submission in submissions:
                        submission._fetched_at = datetime.now()
                        self.__cache[submission.user_id] = (submission, to_include)

                    self.__all_fetched = datetime.now()
            else:

                logger.info(f"Fetching all submissions for assignment id={self.id}")
                start_fetch = time.perf_counter()
                submissions = list(get_submissions(self, include=list(to_include)))
                fetch_elapsed = time.perf_counter() - start_fetch
                logger.info(
                    f"Bulk refresh: {len(submissions)} submissions in "
                    f"{fetch_elapsed:.2f}s"
                )

                for submission in submissions:
                    submission._fetched_at = datetime.now()
                    self.__cache[submission.user_id] = (submission, to_include)

                self.__all_fetched = datetime.now()

            return [submission for submission, _ in self.__cache.values()]

        cls.get_submissions = new_get_submissions
        return cls

    canvasapi.assignment.Assignment = cache_submissions(canvasapi.assignment.Assignment)


def must_refresh(uid, to_include, cache):
    """
    Returns True if the submission needs refreshing based on kwargs.
    """
    cache_status = ""
    if uid in cache:
        submission, included = cache[uid]
        if not to_include.issubset(set(included)):
            cache_status = " (new include required)"
            submission = None
            to_include |= set(included)
    else:
        cache_status = " (not found)"
        submission = None

    if submission:
        if not outdated(submission):
            logger.info(f"Cache hit: submission user_id={uid}")
            return False
        elif not cache_status:
            reason = get_staleness_reason(submission)
            cache_status = f" (stale: {reason})" if reason else " (stale)"

    logger.info(f"Cache miss{cache_status}: submission user_id={uid}")
    return True


# Loads all hacks
this_module = sys.modules[__name__]

# automatically execute all make_* functions to apply decorators
for name, function in inspect.getmembers(this_module, inspect.isfunction):
    if name.startswith("make_"):
        function()
