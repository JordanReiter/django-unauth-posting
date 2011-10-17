import urlparse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib import messages
from django.shortcuts import render
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
import time, os

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json
        
from models import SavedRequest, SavedRequestFile

def get_saved_data(request):
    request_key = request.REQUEST.get('_upreq', False)
    try:
        if request_key:
            assert request.session.get('_upreq',{}).has_key(request.path)
            assert int(request.session['_upreq'][request.path]) == int(request_key)
            try:
                saved_req = SavedRequest.objects.get(key=request_key)
            except SavedRequest.DoesNotExist:
                pass
            else:
                if request.method == 'POST' and len(request.POST):
                    # use the values submitted from the form
                    SAVED_POST = request.POST.copy()
                else:
                    SAVED_POST = {}
                    for k, v in saved_req.data.items():
                        SAVED_POST[k] = v
                SAVED_FILES = {}
                for saved_file in saved_req.files.all():
                    SAVED_FILES[saved_file.name]=SimpleUploadedFile(os.path.basename(saved_file.file.path), saved_file.file.read(), saved_file.content_type)
            return SAVED_POST, SAVED_FILES, request_key
    except AssertionError, inst:
        pass
    return request.POST, request.FILES, False

def save_record(request, form, files=None, success_message=None, redirect_url=None):
    if not form.is_valid():
        raise forms.ValidationError("There were errors in the form.")
    if files:
        form.cleaned_data.update(files)
    model = form.save()
    
    if success_message:
        messages.success(request, success_message % form.cleaned_data)
    return HttpResponseRedirect(redirect_url or model.get_absolute_url())

def handle_saved_data(request, form_class, args=[], kwargs={}, action=None, 
                      confirm_message=None, success_message=None, 
                      redirect_url=None, template_name="unauth_posting/confirm.html", **extra_context):
    request_key = request.REQUEST.get('_upreq', False)
    SAVED_POST, SAVED_FILES, request_key = get_saved_data(request)
    if request.method == 'POST':
        form = form_class(data=SAVED_POST, files=SAVED_FILES, *args, **kwargs)
        resp = save_record(request, form, files=SAVED_FILES, success_message=success_message, redirect_url=redirect_url)
        del request.session['_upreq'][request.path]
        return resp
    else:
        form = form_class(data=SAVED_POST, files=SAVED_FILES, *args, **kwargs)
        for f, _ in form.fields.items():
            if f in SAVED_FILES.keys():
                del form.fields[f]
            else:
                form.fields[f].widget = forms.HiddenInput()
    ctx = locals()
    ctx.update(extra_context)
    return render(request, template_name, ctx)

def save_if_authenticated(request, form, redirect_url=None,  
                          success_message=None, login_message=None,
                          login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
                          ):
    """
    If the user is authenticated, it saves the model and redirects to
    either a given redirect url or the `absolute_url` of the newly created record.
    
    If the user is not authenticated, the data is saved for later retrieval.
    
    In order to add a success message (when model is saved) or a failure message (when login is required)
    You can include either `success_message` or `login_message`. In both cases, you can access items of the 
    submitted form like so:
        success_message="You submitted a record with the title %(title)s"
    and the function will put in the value from the `title` field.

    """
    if request.user.is_authenticated():
        return save_record(request, form, files=None, success_message=success_message, redirect_url=redirect_url)
    else:
        if login_message:
            messages.info(request, login_message % form.cleaned_data)
        request_key = int(time.time()*10)
        request.session.setdefault('_upreq',{})[request.path]=request_key
        saved_req = SavedRequest.objects.create(
                                                data=json.dumps(request.POST.copy()),
                                                key = request_key
                                                )
        for key, file in request.FILES.items():
            SavedRequestFile.objects.create(
                                            request = saved_req,
                                            file = file,
                                            name = key,
                                            content_type = file.content_type 
                                            )
        """
         swiped from django.contrib.decorators.user_passes_test
         """
        path = request.build_absolute_uri()
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse.urlparse(login_url or
                                                    settings.LOGIN_URL)[:2]
        current_scheme, current_netloc = urlparse.urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
            (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        path += '&' if '?' in path else '?'
        path += '_upreq=%s' % request_key
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path, login_url, redirect_field_name)
