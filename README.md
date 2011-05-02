django-unauth-posting

This django-app allows users to submit forms even if they aren't authenticated.

Once they hit submit, and the form is validated, they are redirected to 
the login url (either provided as a variable or settings.LOGIN_URL). So long
as your authentication redirects to the value stored in `REDIRECT_FIELD_NAME` (i.e. next),
in the next step a confirmation form will be displayed; submitting the form 
will save the record by calling the form's `save` method.

To install, add `'unauth_posting'` to `INSTALLED_APPS` in the settings.py file.

unauth_posting must be added on a per-view basis. Here's an example:

    def test_view(request, form_class=TestForm, template_name="test/form.html"):
        success_message = 'New foo %(title)s saved'
        login_message = "You must log in before you can finish creating your test foo."
        SAVED_POST, SAVED_FILES, saved_key = get_saved_data(request)
        if saved_key:
            try:
                return handle_saved_data(request, form_class, action="Save test record", 
                                         success_message=success_message )
            except ValidationError:
                pass
        if request.method == 'POST':
            form = TestForm(data=SAVED_POST, files=SAVED_FILES)
            if form.is_valid():
                return save_if_authenticated(request, form, success_message=success_message,
                                             login_message=login_message,
                                             )
        else:
            form = TestForm()
        return render_to_response(template_name, locals(), RequestContext(request))
    

`get_saved_data` returns a tuple of the saved `request.POST` values, the saved `request.FILES`, and `True` if the data was retrieved from saved values and `False` if it simply came from the request object.

`handle_saved_data` retrieves the saved data to be processed. If the method is POST, then the data is saved. Otherwise a confirmation form is displayed so that the user can confirm the form (because the data must be submitted as part of a POST request).

`save_if_authenticated` saves the form if the user is logged in. If not; it saves the data in the form, as well as any uploaded files, and redirects the user to the login page.

Again, make sure that after login, the user is redirected back to the URL specified by the `next` (`REDIRECT_FIELD_NAME`) variable sent to the login page.
