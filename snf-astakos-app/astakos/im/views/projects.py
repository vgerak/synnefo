# Copyright 2011-2012 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

import logging
import calendar
import inflect

engine = inflect.engine()

from urllib import quote
from functools import wraps
from datetime import datetime
from synnefo.lib.ordereddict import OrderedDict

from django_tables2 import RequestConfig

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import (
    HttpResponse, HttpResponseBadRequest,
    HttpResponseForbidden, HttpResponseRedirect,
    HttpResponseBadRequest, Http404)
from django.shortcuts import redirect
from django.template import RequestContext, loader as template_loader
from django.utils.http import urlencode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic.create_update import (
    apply_extra_context, lookup_object, delete_object, get_model_and_form_class)
from django.views.generic.list_detail import object_list, object_detail
from django.core.xheaders import populate_xheaders
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import simplejson as json
from django.contrib.auth.views import redirect_to_login

from synnefo_branding.utils import render_to_string
from snf_django.lib.db.transaction import commit_on_success_strict

import astakos.im.messages as astakos_messages

from astakos.im import activation_backends
from astakos.im import tables
from astakos.im.models import (
    AstakosUser, ApprovalTerms,
    EmailChange, AstakosUserAuthProvider, PendingThirdPartyUser,
    ProjectApplication, ProjectMembership, Project, Service, Resource)
from astakos.im.util import (
    get_context, prepare_response, get_query, restrict_next, model_to_dict)
from astakos.im.forms import (
    LoginForm, InvitationForm,
    FeedbackForm, SignApprovalTermsForm,
    EmailChangeForm,
    ProjectApplicationForm, ProjectSortForm,
    AddProjectMembersForm, ProjectSearchForm,
    ProjectMembersSortForm)
from astakos.im.forms import ExtendedProfileForm as ProfileForm
from astakos.im.functions import (
    send_feedback,
    logout as auth_logout,
    invite as invite_func,
    check_pending_app_quota,
    accept_membership, reject_membership, remove_membership, cancel_membership,
    leave_project, join_project, enroll_member, can_join_request,
    can_leave_request,
    get_related_project_id, get_by_chain_or_404,
    approve_application, deny_application,
    cancel_application, dismiss_application)
from astakos.im.settings import (
    COOKIE_DOMAIN, LOGOUT_NEXT,
    LOGGING_LEVEL, PAGINATE_BY,
    PAGINATE_BY_ALL,
    ACTIVATION_REDIRECT_URL,
    MODERATION_ENABLED)
from astakos.im import presentation
from astakos.im import settings
from astakos.im import auth_providers as auth
from snf_django.lib.db.transaction import commit_on_success_strict
from astakos.im.ctx import ExceptionHandler
from astakos.im import quotas
from astakos.im.views.util import render_response, _create_object, \
    _update_object, _resources_catalog
from astakos.im.views.decorators import cookie_fix, signed_terms_required,\
    required_auth_methods_assigned, valid_astakos_user_required

logger = logging.getLogger(__name__)


@cookie_fix
def how_it_works(request):
    return render_response(
        'im/how_it_works.html',
        context_instance=get_context(request))


@require_http_methods(["GET", "POST"])
@cookie_fix
@valid_astakos_user_required
def project_add(request):
    user = request.user
    if not user.is_project_admin():
        ok, limit = check_pending_app_quota(user)
        if not ok:
            m = _(astakos_messages.PENDING_APPLICATION_LIMIT_ADD) % limit
            messages.error(request, m)
            next = reverse('astakos.im.views.project_list')
            next = restrict_next(next, domain=COOKIE_DOMAIN)
            return redirect(next)

    details_fields = ["name", "homepage", "description", "start_date",
                      "end_date", "comments"]
    membership_fields = ["member_join_policy", "member_leave_policy",
                         "limit_on_members_number"]
    resource_catalog, resource_groups = _resources_catalog(for_project=True)
    if resource_catalog is False:
        # on fail resource_groups contains the result object
        result = resource_groups
        messages.error(request, 'Unable to retrieve system resources: %s' %
                       result.reason)
    extra_context = {
        'resource_catalog': resource_catalog,
        'resource_groups': resource_groups,
        'show_form': True,
        'details_fields': details_fields,
        'membership_fields': membership_fields}

    response = None
    with ExceptionHandler(request):
        response = _create_object(
            request,
            template_name='im/projects/projectapplication_form.html',
            extra_context=extra_context,
            post_save_redirect=reverse('project_list'),
            form_class=ProjectApplicationForm,
            msg=_("The %(verbose_name)s has been received and "
                  "is under consideration."),
            )

    if response is not None:
        return response

    next = reverse('astakos.im.views.project_list')
    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)


@require_http_methods(["GET"])
@cookie_fix
@valid_astakos_user_required
def project_list(request):
    projects = ProjectApplication.objects.user_accessible_projects(request.user).select_related()
    table = tables.UserProjectApplicationsTable(projects, user=request.user,
                                                prefix="my_projects_")
    RequestConfig(request, paginate={"per_page": PAGINATE_BY}).configure(table)

    return object_list(
        request,
        projects,
        template_name='im/projects/project_list.html',
        extra_context={
            'is_search':False,
            'table': table,
        })


@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_app_cancel(request, application_id):
    next = request.GET.get('next')
    chain_id = None

    with ExceptionHandler(request):
        chain_id = _project_app_cancel(request, application_id)

    if not next:
        if chain_id:
            next = reverse('astakos.im.views.project_detail', args=(chain_id,))
        else:
            next = reverse('astakos.im.views.project_list')

    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)

@commit_on_success_strict()
def _project_app_cancel(request, application_id):
    chain_id = None
    try:
        application_id = int(application_id)
        chain_id = get_related_project_id(application_id)
        cancel_application(application_id, request.user)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)

    else:
        msg = _(astakos_messages.APPLICATION_CANCELLED)
        messages.success(request, msg)
        return chain_id


@require_http_methods(["GET", "POST"])
@cookie_fix
@valid_astakos_user_required
def project_modify(request, application_id):

    try:
        app = ProjectApplication.objects.get(id=application_id)
    except ProjectApplication.DoesNotExist:
        raise Http404

    user = request.user
    if not (user.owns_application(app) or user.is_project_admin(app.id)):
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    if not user.is_project_admin():
        owner = app.owner
        ok, limit = check_pending_app_quota(owner, precursor=app)
        if not ok:
            m = _(astakos_messages.PENDING_APPLICATION_LIMIT_MODIFY) % limit
            messages.error(request, m)
            next = reverse('astakos.im.views.project_list')
            next = restrict_next(next, domain=COOKIE_DOMAIN)
            return redirect(next)

    details_fields = ["name", "homepage", "description", "start_date",
                      "end_date", "comments"]
    membership_fields = ["member_join_policy", "member_leave_policy",
                         "limit_on_members_number"]
    resource_catalog, resource_groups = _resources_catalog(for_project=True)
    if resource_catalog is False:
        # on fail resource_groups contains the result object
        result = resource_groups
        messages.error(request, 'Unable to retrieve system resources: %s' %
                       result.reason)
    extra_context = {
        'resource_catalog': resource_catalog,
        'resource_groups': resource_groups,
        'show_form': True,
        'details_fields': details_fields,
        'update_form': True,
        'membership_fields': membership_fields
    }

    response = None
    with ExceptionHandler(request):
        response = _update_object(
            request,
            object_id=application_id,
            template_name='im/projects/projectapplication_form.html',
            extra_context=extra_context,
            post_save_redirect=reverse('project_list'),
            form_class=ProjectApplicationForm,
            msg=_("The %(verbose_name)s has been received and is under "
                  "consideration."))

    if response is not None:
        return response

    next = reverse('astakos.im.views.project_list')
    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)

@require_http_methods(["GET", "POST"])
@cookie_fix
@valid_astakos_user_required
def project_app(request, application_id):
    return common_detail(request, application_id, project_view=False)

@require_http_methods(["GET", "POST"])
@cookie_fix
@valid_astakos_user_required
def project_detail(request, chain_id):
    return common_detail(request, chain_id)

@commit_on_success_strict()
def addmembers(request, chain_id, addmembers_form):
    if addmembers_form.is_valid():
        try:
            chain_id = int(chain_id)
            map(lambda u: enroll_member(
                    chain_id,
                    u,
                    request_user=request.user),
                addmembers_form.valid_users)
        except (IOError, PermissionDenied), e:
            messages.error(request, e)

def common_detail(request, chain_or_app_id, project_view=True):
    project = None
    if project_view:
        chain_id = chain_or_app_id
        if request.method == 'POST':
            addmembers_form = AddProjectMembersForm(
                request.POST,
                chain_id=int(chain_id),
                request_user=request.user)
            with ExceptionHandler(request):
                addmembers(request, chain_id, addmembers_form)

            if addmembers_form.is_valid():
                addmembers_form = AddProjectMembersForm()  # clear form data
        else:
            addmembers_form = AddProjectMembersForm()  # initialize form

        project, application = get_by_chain_or_404(chain_id)
        if project:
            members = project.projectmembership_set.select_related()
            members_table = tables.ProjectMembersTable(project,
                                                       members,
                                                       user=request.user,
                                                       prefix="members_")
            RequestConfig(request, paginate={"per_page": PAGINATE_BY}
                          ).configure(members_table)

        else:
            members_table = None

    else: # is application
        application_id = chain_or_app_id
        application = get_object_or_404(ProjectApplication, pk=application_id)
        members_table = None
        addmembers_form = None

    modifications_table = None

    user = request.user
    is_project_admin = user.is_project_admin(application_id=application.id)
    is_owner = user.owns_application(application)
    if not (is_owner or is_project_admin) and not project_view:
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    if (not (is_owner or is_project_admin) and project_view and
        not user.non_owner_can_view(project)):
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    following_applications = list(application.pending_modifications())
    following_applications.reverse()
    modifications_table = (
        tables.ProjectModificationApplicationsTable(following_applications,
                                                    user=request.user,
                                                    prefix="modifications_"))

    mem_display = user.membership_display(project) if project else None
    can_join_req = can_join_request(project, user) if project else False
    can_leave_req = can_leave_request(project, user) if project else False

    return object_detail(
        request,
        queryset=ProjectApplication.objects.select_related(),
        object_id=application.id,
        template_name='im/projects/project_detail.html',
        extra_context={
            'project_view': project_view,
            'addmembers_form':addmembers_form,
            'members_table': members_table,
            'owner_mode': is_owner,
            'admin_mode': is_project_admin,
            'modifications_table': modifications_table,
            'mem_display': mem_display,
            'can_join_request': can_join_req,
            'can_leave_request': can_leave_req,
            })

@require_http_methods(["GET", "POST"])
@cookie_fix
@valid_astakos_user_required
def project_search(request):
    q = request.GET.get('q', '')
    form = ProjectSearchForm()
    q = q.strip()

    if request.method == "POST":
        form = ProjectSearchForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data['q'].strip()
        else:
            q = None

    if q is None:
        projects = ProjectApplication.objects.none()
    else:
        accepted_projects = request.user.projectmembership_set.filter(
            ~Q(acceptance_date__isnull=True)).values_list('project', flat=True)
        projects = ProjectApplication.objects.search_by_name(q)
        projects = projects.filter(~Q(project__last_approval_date__isnull=True))
        projects = projects.exclude(project__in=accepted_projects)

    table = tables.UserProjectApplicationsTable(projects, user=request.user,
                                                prefix="my_projects_")
    if request.method == "POST":
        table.caption = _('SEARCH RESULTS')
    else:
        table.caption = _('ALL PROJECTS')

    RequestConfig(request, paginate={"per_page": PAGINATE_BY}).configure(table)

    return object_list(
        request,
        projects,
        template_name='im/projects/project_list.html',
        extra_context={
          'form': form,
          'is_search': True,
          'q': q,
          'table': table
        })

@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_join(request, chain_id):
    next = request.GET.get('next')
    if not next:
        next = reverse('astakos.im.views.project_detail',
                       args=(chain_id,))

    with ExceptionHandler(request):
        _project_join(request, chain_id)


    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)


@commit_on_success_strict()
def _project_join(request, chain_id):
    try:
        chain_id = int(chain_id)
        auto_accepted = join_project(chain_id, request.user)
        if auto_accepted:
            m = _(astakos_messages.USER_JOINED_PROJECT)
        else:
            m = _(astakos_messages.USER_JOIN_REQUEST_SUBMITTED)
        messages.success(request, m)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)


@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_leave(request, chain_id):
    next = request.GET.get('next')
    if not next:
        next = reverse('astakos.im.views.project_list')

    with ExceptionHandler(request):
        _project_leave(request, chain_id)

    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)


@commit_on_success_strict()
def _project_leave(request, chain_id):
    try:
        chain_id = int(chain_id)
        auto_accepted = leave_project(chain_id, request.user)
        if auto_accepted:
            m = _(astakos_messages.USER_LEFT_PROJECT)
        else:
            m = _(astakos_messages.USER_LEAVE_REQUEST_SUBMITTED)
        messages.success(request, m)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)


@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_cancel(request, chain_id):
    next = request.GET.get('next')
    if not next:
        next = reverse('astakos.im.views.project_list')

    with ExceptionHandler(request):
        _project_cancel(request, chain_id)

    next = restrict_next(next, domain=COOKIE_DOMAIN)
    return redirect(next)


@commit_on_success_strict()
def _project_cancel(request, chain_id):
    try:
        chain_id = int(chain_id)
        cancel_membership(chain_id, request.user)
        m = _(astakos_messages.USER_REQUEST_CANCELLED)
        messages.success(request, m)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)



@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_accept_member(request, chain_id, memb_id):

    with ExceptionHandler(request):
        _project_accept_member(request, chain_id, memb_id)

    return redirect(reverse('project_detail', args=(chain_id,)))


@commit_on_success_strict()
def _project_accept_member(request, chain_id, memb_id):
    try:
        chain_id = int(chain_id)
        memb_id = int(memb_id)
        m = accept_membership(chain_id, memb_id, request.user)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)

    else:
        email = escape(m.person.email)
        msg = _(astakos_messages.USER_MEMBERSHIP_ACCEPTED) % email
        messages.success(request, msg)


@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_remove_member(request, chain_id, memb_id):

    with ExceptionHandler(request):
        _project_remove_member(request, chain_id, memb_id)

    return redirect(reverse('project_detail', args=(chain_id,)))


@commit_on_success_strict()
def _project_remove_member(request, chain_id, memb_id):
    try:
        chain_id = int(chain_id)
        memb_id = int(memb_id)
        m = remove_membership(chain_id, memb_id, request.user)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)
    else:
        email = escape(m.person.email)
        msg = _(astakos_messages.USER_MEMBERSHIP_REMOVED) % email
        messages.success(request, msg)


@require_http_methods(["POST"])
@cookie_fix
@valid_astakos_user_required
def project_reject_member(request, chain_id, memb_id):

    with ExceptionHandler(request):
        _project_reject_member(request, chain_id, memb_id)

    return redirect(reverse('project_detail', args=(chain_id,)))


@commit_on_success_strict()
def _project_reject_member(request, chain_id, memb_id):
    try:
        chain_id = int(chain_id)
        memb_id = int(memb_id)
        m = reject_membership(chain_id, memb_id, request.user)
    except (IOError, PermissionDenied), e:
        messages.error(request, e)
    else:
        email = escape(m.person.email)
        msg = _(astakos_messages.USER_MEMBERSHIP_REJECTED) % email
        messages.success(request, msg)


@require_http_methods(["POST"])
@signed_terms_required
@login_required
@cookie_fix
def project_app_approve(request, application_id):

    if not request.user.is_project_admin():
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    try:
        app = ProjectApplication.objects.get(id=application_id)
    except ProjectApplication.DoesNotExist:
        raise Http404

    with ExceptionHandler(request):
        _project_app_approve(request, application_id)

    chain_id = get_related_project_id(application_id)
    return redirect(reverse('project_detail', args=(chain_id,)))


@commit_on_success_strict()
def _project_app_approve(request, application_id):
    approve_application(application_id)


@require_http_methods(["POST"])
@signed_terms_required
@login_required
@cookie_fix
def project_app_deny(request, application_id):

    reason = request.POST.get('reason', None)
    if not reason:
        reason = None

    if not request.user.is_project_admin():
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    try:
        app = ProjectApplication.objects.get(id=application_id)
    except ProjectApplication.DoesNotExist:
        raise Http404

    with ExceptionHandler(request):
        _project_app_deny(request, application_id, reason)

    return redirect(reverse('project_list'))


@commit_on_success_strict()
def _project_app_deny(request, application_id, reason):
    deny_application(application_id, reason=reason)


@require_http_methods(["POST"])
@signed_terms_required
@login_required
@cookie_fix
def project_app_dismiss(request, application_id):
    try:
        app = ProjectApplication.objects.get(id=application_id)
    except ProjectApplication.DoesNotExist:
        raise Http404

    if not request.user.owns_application(app):
        m = _(astakos_messages.NOT_ALLOWED)
        raise PermissionDenied(m)

    with ExceptionHandler(request):
        _project_app_dismiss(request, application_id)

    chain_id = None
    chain_id = get_related_project_id(application_id)
    if chain_id:
        next = reverse('project_detail', args=(chain_id,))
    else:
        next = reverse('project_list')
    return redirect(next)


def _project_app_dismiss(request, application_id):
    # XXX: dismiss application also does authorization
    dismiss_application(application_id, request_user=request.user)