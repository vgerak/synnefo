# Copyright 2013 GRNET S.A. All rights reserved.
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

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.utils import simplejson as json

from snf_django.lib.db.transaction import commit_on_success_strict
from astakos.im.register import add_service, ServiceException
from astakos.im.models import Component


class Command(BaseCommand):
    help = "Register services"

    option_list = BaseCommand.option_list + (
        make_option('--json',
                    dest='json',
                    metavar='<json.file>',
                    help="Load service definitions from a json file"),
    )

    @commit_on_success_strict()
    def handle(self, *args, **options):

        json_file = options['json']
        if not json_file:
            m = "Expecting option --json."
            raise CommandError(m)

        else:
            with open(json_file) as file_data:
                m = ('Input should be a JSON dict mapping service names '
                     'to definitions.')
                try:
                    data = json.load(file_data)
                except json.JSONDecodeError:
                    raise CommandError(m)
                if not isinstance(data, dict):
                    raise CommandError(m)
        self.add_services(data)

    def add_services(self, data):
        write = self.stdout.write
        output = []
        for name, service_dict in data.iteritems():
            try:
                component_name = service_dict['component']
                service_type = service_dict['type']
                endpoints = service_dict['endpoints']
            except KeyError:
                raise CommandError('Malformed service definition.')

            try:
                component = Component.objects.get(name=component_name)
            except Component.DoesNotExist:
                m = "Component '%s' is not registered." % component_name
                raise CommandError(m)

            try:
                existed = add_service(component, name, service_type, endpoints)
            except ServiceException as e:
                raise CommandError(e.message)

            m = "%s service %s.\n" % ("Updated" if existed else "Added", name)
            output.append(m)

        for line in output:
            write(line)
