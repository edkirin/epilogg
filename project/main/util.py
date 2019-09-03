from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import urlunquote_plus

import re
import os
import hashlib
import random
import logging
import datetime

import project.main.const as const
import project.settings


#--------------------------------------------------------------------------------------------------


def get_site_url():
    return project.settings.local.SiteURL


#--------------------------------------------------------------------------------------------------


def unescape(text):
    """Removes HTML or XML character references
       and entities from a text string.
       keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """

    import htmlentitydefs

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                   return unichr(int(text[3:-1], 16))
                else:
                   return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                if text[1:-1] == "amp":
                    text = "&amp;amp;"
                elif text[1:-1] == "gt":
                    text = "&amp;gt;"
                elif text[1:-1] == "lt":
                    text = "&amp;lt;"
                else:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


#--------------------------------------------------------------------------------------------------


def get_image_type(filename):
    import os.path
    filename_info = os.path.splitext(filename)
    ext = filename_info[1].lower()
    if ext in [".jpg", ".jpeg"]:
        return "JPEG"
    elif ext == ".png":
        return "PNG"
    elif ext == ".gif":
        return "GIF"
    elif ext == ".swf":
        return "SWF"
    else:
        return ""


#--------------------------------------------------------------------------------------------------


def create_image_filename_with_ext(original_filename, suggested_name):
    import os.path
    import random
    from django.template.defaultfilters import slugify

    filename_info = os.path.splitext(original_filename)
    ext = filename_info[1].lower()
    sha = hashlib.sha1("%f" % (random.random())).hexdigest()

    return "%s_%s%s" % (slugify(suggested_name), sha[0:6], ext)


#--------------------------------------------------------------------------------------------------


def create_image_filename(id, suggested_name="", suggested_ext=""):
    import os.path
    import string
    import random
    from django.template.defaultfilters import slugify

    #filename_info = os.path.splitext(original_filename)
    #ext = string.lower(filename_info[1])

    if suggested_ext:
        ext = "." + suggested_ext
    else:
        ext = ".jpg"

    sha = hashlib.sha1("%s %f" % (id, random.random())).hexdigest()

    if len(suggested_name) != 0:
        return "%s_%s%s" % (slugify(suggested_name), sha[0:6], ext)
    else:
        return "%06d_%s%s" % (id, sha[0 : 20], ext)


#--------------------------------------------------------------------------------------------------


def resize_image_stream(stream, size, force_width=True):
    import PIL
    from PIL import Image
    PIL.Image.init()
    import StringIO
    from django.core.files.base import ContentFile

    def get_file_ext(img):
        if img.format == "GIF":
            return "gif"
        elif img.format == "JPEG":
            return "jpg"
        elif img.format == "PNG":
            return "png"
        else:
            return ""

    try:
        img = PIL.Image.open(stream)

        w, h = size
        img_w, img_h = img.size

        output = StringIO.StringIO()

        if img_w > w:
            if force_width:
                if img_w < img_h:
                    h = int((float(img_h) / float(img_w)) * w)
                    size = (w, h)

            img = img.convert("RGB")
            img.thumbnail(size, PIL.Image.ANTIALIAS)
            img.save(output, format= 'JPEG')
            contents = output.getvalue()
            output.close()

            return (ContentFile(contents), "jpg")
        else:
            return (stream, get_file_ext(img))
    except:
        return (stream, "")


#--------------------------------------------------------------------------------------------------


def resize_image(filename, size, force_width):
    import PIL
    from PIL import Image
    PIL.Image.init()

    try:
        img = PIL.Image.open(filename)
        if img.mode != "RGB": img = img.convert("RGB")

        if force_width:
            w, h = size
            img_w, img_h = img.size

            if img_w < img_h:
                h = int((float(img_h) / float(img_w)) * w)
                size = (w, h)

        img.thumbnail(size, PIL.Image.ANTIALIAS)
        img.save(filename)
        return True
    except:
        return False


#--------------------------------------------------------------------------------------------------


def send_mail(to, subject, body, is_html=False, reply_to="", attachment=None):
    from django.core.mail import EmailMessage
    from project.main.models import Settings

    log = logging.getLogger('mail')
    log.info(u'Sending mail to {mail_to}, subject: {subject}'.format(mail_to=to, subject=subject))
    settings = Settings.read()

    if not is_html:
        body += "\n\n-- \n" + project.settings.local.SiteURL

    headers = {"From": "%s <%s>" % (settings.shop_name, settings.info_email)}

    if reply_to != "":
        headers.update({"Reply-To": reply_to})

    if not isinstance(to, list):
        to = [to]

    email = EmailMessage(subject, body, to=to, headers=headers)

    if is_html:
        email.content_subtype = "html"

    if attachment != None:
        (filename, content, mime) = attachment
        email.attach(filename, content, mime)

    try:
        email.send()
        return True
    except:
        return False


#--------------------------------------------------------------------------------------------------


def str_to_float(s, default = 0.0):
    try:
        return float(s.replace(",", "."))
    except:
        return default


#--------------------------------------------------------------------------------------------------


def str_to_int(s, default=0):
    try:
        return int(s)
    except:
        return default


#--------------------------------------------------------------------------------------------------


def str_to_date(s):
    date = s.replace(",", ".").split(".")
    res = None
    try:
        if len(date) >= 3:
            res = datetime.date(int(date[2]), int(date[1]), int(date[0]))
    except:
        pass

    return res


#--------------------------------------------------------------------------------------------------


def str_to_time(s, default=None):
    res = default
    try:
        hh, mm = s.strip().split(':')
        res = datetime.time(hour=int(hh), minute=int(mm))
    except:
        pass
    return res

#--------------------------------------------------------------------------------------------------


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url='/login/',
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


#--------------------------------------------------------------------------------------------------


def staff_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, role=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser or (u.is_staff and (role is None or u.has_role(role))),
        login_url='/login/',
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


#--------------------------------------------------------------------------------------------------


def user_role_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, role=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser or (u.is_authenticated and (role is None or u.custom.has_role(role))),
        login_url='/login/',
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


#--------------------------------------------------------------------------------------------------


def xstaff_required(role):
    def wrapper(function):
        def inner(*args, **kwargs):
            request = args[0]
            user = request.user
            if user.is_authenticated():
                if user.is_superuser or (user.is_staff and user.has_role(role)):
                    # allow superusers and matching role to enter the view
                    return function(*args, **kwargs)
                elif user.is_staff:
                    pass
                    # if role don't match, redirect to appropriate admin frontpage
                    if user.has_role(const.UserRoleBlogEditor):
                        return HttpResponseRedirect("/administrator/blog/")
                    elif user.has_role(const.UserRoleConsultant):
                        return HttpResponseRedirect("/administrator/consult/")
                    else:
                        raise Http404
                else:
                    # for nonstaff, raise 404
                    raise Http404
            else:
                redirect = "/administrator/login/?next={}".format(request.path)
                return HttpResponseRedirect(redirect)
        return inner
    return wrapper


#--------------------------------------------------------------------------------------------------


def decode_cookie_value(s):
    # cookie value is urlencoded, decode hr chars
    return urlunquote_plus(str(s))


#--------------------------------------------------------------------------------------------------


def create_hash_filepath(base_path, create_filename=True, ext=None, depth=2, create_dirs=True):
    # add trailing slash to base dir
    if not base_path.endswith('/'):
        base_path += '/'

    # create path hash
    path_hash = hashlib.sha1(str(random.random())).hexdigest()
    s = [path_hash[i:i+2] for i in range(0, len(path_hash), 2)]

    rel_path = '/'.join(s[:depth]) + '/'
    path = base_path + rel_path

    if create_dirs and not os.path.exists(path):
        os.makedirs(path)

    if create_filename:
        file_name = hashlib.sha1(str(random.random())).hexdigest()
        if ext is not None:
            if not ext.startswith('.'):
                ext = '.' + ext
            file_name += ext
        file_path = path + file_name
    else:
        file_name = file_path = ""

    res = {
        "path": path,
        "rel_path": rel_path,
        "file_name": file_name,
        "file_path": file_path,
    }

    return res


#--------------------------------------------------------------------------------------------------


def get_ip_from_request(request):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    # it's possible to have more than one address in this field (client ip, proxy1, proxy2...). take first one!
    ip = ip.split(",")[0]
    return ip


#--------------------------------------------------------------------------------------------------
