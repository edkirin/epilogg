from django.db.models import Q

import datetime

from project.main.util import str_to_int


#**************************************************************************************************


class AdminSetter(object):

    #----------------------------------------------------------------------------------------------

    def set_string(self, attr, value):
        from django.db.models.fields import CharField as CharField
        value = value.strip() if value is not None else ""

        # if field is CharField, limit the length
        model_attr = self._meta.get_field(attr)
        if isinstance(model_attr, CharField):
            value = value[:model_attr.max_length]

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_int(self, attr, value, default=0, min_value=None, max_value=None):
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = default

        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_float(self, attr, value, default=0.0, min_value=None, max_value=None):
        try:
            value = float(value.replace(",", "."))
        except (ValueError, TypeError):
            value = default

        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_bool(self, attr, value):
        setattr(self, attr, value not in [None, ""])

    #----------------------------------------------------------------------------------------------

    def set_date(self, attr, value):
        try:
            dd, mm, yy = value.strip(".").split(".")
            value = datetime.date(int(yy), int(mm), int(dd))
        except:
            value = None

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_datetime(self, attr, value):
        try:
            date, time = value.split(" ")
            dd, mm, yy = date.split(".")
            try:
                hh, min = time.split(":")
            except:
                hh = min = 0
            value = datetime.datetime(str_to_int(yy), str_to_int(mm), str_to_int(dd), str_to_int(hh), str_to_int(min), 0)
        except Exception:
            value = None

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_iso_datetime(self, attr, value):
        try:
            date, time = value.split(" ")
            yy, mm, dd = date.split("-")
            try:
                hh, min, sec = time.split(":")
            except:
                hh = min = sec = 0
            value = datetime.datetime(str_to_int(yy), str_to_int(mm), str_to_int(dd), str_to_int(hh), str_to_int(min), str_to_int(sec))
        except Exception:
            value = None

        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_foreign_object(self, attr, obj_class, id):
        try:
            value = obj_class.objects.get(id=id)
        except:
            value = None
        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    def set_many_to_many(self, attr, obj_class, ids):
        if isinstance(ids, str):
            ids = [str_to_int(n) for n in ids.split(",") if n]

        # add new objects
        for id in ids:
            try:
                item = obj_class.objects.get(id=id)
                if not attr.filter(id=id).exists():
                    attr.add(item)
            except obj_class.DoesNotExist:
                pass
        # remove nonexisting objects
        for item in attr.all():
            if item.id not in ids:
                attr.remove(item)

    #----------------------------------------------------------------------------------------------

    def set_ordering(self, order_changed, order_items_ids):
        if order_changed == "1":
            ids = [str_to_int(n) for n in order_items_ids.split(",") if n]
            for n, id in enumerate(ids):
                if id == 0:
                    id = self.id
                self.__class__.objects.filter(id=id).update(order=n)

    #----------------------------------------------------------------------------------------------

    def split_string(self, attr, max_count=5, separator='|'):
        value = getattr(self, attr)
        return ([s for s in value.split(separator) if len(s) > 0] + [""] * max_count)[:max_count]

    #----------------------------------------------------------------------------------------------

    def join_string(self, attr, value, separator='|'):
        value = separator.join([s.strip() for s in value if len(s.strip()) > 0])
        setattr(self, attr, value)

    #----------------------------------------------------------------------------------------------

    @classmethod
    def create_object(cls, id, select_related=None):
        try:
            id = int(id)
        except ValueError:
            id = 0

        new_item = id == 0
        item = None

        if not new_item:
            try:
                if select_related is None:
                    item = cls.objects.get(id=id)
                else:
                    item = cls.objects.select_related(*select_related).get(id=id)
            except:
                new_item = True

        if new_item:
            item = cls()
        return item, new_item

    #----------------------------------------------------------------------------------------------

    @classmethod
    def set_publish_objects(cls, ids, state):
        cls.objects.filter(id__in=ids).update(published=state)

    #----------------------------------------------------------------------------------------------

    @classmethod
    def delete_objects(cls, ids):
        for id in ids:
            try:
                item = cls.objects.get(id=id)
                item.delete()
            except cls.DoesNotExist:
                pass

    #----------------------------------------------------------------------------------------------

    @classmethod
    def normalize_order(cls, filter=None):
        items = cls.objects.all() if filter is None else cls.objects.filter(filter)
        for n, item in enumerate(items):
            item.order = n
            item.save(update_fields=["order"])

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************


class ObjectCachePool(object):
    cls = None
    items = None
    flat_items = None

    def __init__(self, cls):
        self.cls = cls
        self.items = {}
        self.flat_items = []

    def load(self, ids, ordering=None, related=None, only=None):
        ids = list(set(ids))  # remove duplicates
        self.load_from_query(
            q=Q(id__in=ids),
            ordering=ordering,
            related=related,
            only=only
        )

    def load_from_query(self, q, ordering=None, related=None, prefetch=None, only=None):
        objects = self.cls.objects.filter(q)
        if related is not None:
            objects = objects.select_related(*related)
        if prefetch is not None:
            objects = objects.prefetch_related(*prefetch)
        if ordering is not None:
            objects = objects.order_by(*ordering)
        if only is not None:
            objects = objects.only(*only)

        self.load_from_list(objects)

    def load_from_list(self, objects):
        for item in objects:
            self.items.update({
                item.id: item,
            })
            self.flat_items.append(item)

    def get_item(self, id):
        if id is None:
            return None

        if id in self.items:
            return self.items[id]

        try:
            item = self.cls.objects.get(id=id)
        except self.cls.DoesNotExist:
            item = None

        if item is not None:
            self.items.update({
                item.id: item,
            })

        return item

    def get_all_items(self):
        return self.flat_items

    def get_item_ids(self):
        return [c.id for c in self.flat_items]


#**************************************************************************************************
