# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Removing unique constraint on 'Resource', fields ['name', 'service']
        db.delete_unique('im_resource', ['name', 'service_id'])

        # Deleting model 'ResourceMetadata'
        db.delete_table('im_resourcemetadata')

        # Deleting field 'AstakosUserQuota.import_limit'
        db.delete_column('im_astakosuserquota', 'import_limit')

        # Deleting field 'AstakosUserQuota.export_limit'
        db.delete_column('im_astakosuserquota', 'export_limit')

        # Deleting field 'AstakosUserQuota.quantity'
        db.delete_column('im_astakosuserquota', 'quantity')

        # Deleting field 'Service.order'
        db.delete_column('im_service', 'order')

        # Deleting field 'Service.icon'
        db.delete_column('im_service', 'icon')

        # Adding field 'Service.api_url'
        db.add_column('im_service', 'api_url', self.gf('django.db.models.fields.CharField')(max_length=255, null=True), keep_default=False)

        # Changing field 'Service.url'
        db.alter_column('im_service', 'url', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Deleting field 'Project.is_active'
        db.delete_column('im_project', 'is_active')

        # Deleting field 'Project.is_modified'
        db.delete_column('im_project', 'is_modified')

        # Deleting field 'ProjectMembership.is_active'
        db.delete_column('im_projectmembership', 'is_active')

        # Deleting field 'ProjectMembership.pending_application'
        db.delete_column('im_projectmembership', 'pending_application_id')

        # Deleting field 'ProjectMembership.pending_serial'
        db.delete_column('im_projectmembership', 'pending_serial')

        # Deleting field 'ProjectMembership.application'
        db.delete_column('im_projectmembership', 'application_id')

        # Deleting field 'ProjectMembership.is_pending'
        db.delete_column('im_projectmembership', 'is_pending')

        # Deleting field 'Resource.group'
        db.delete_column('im_resource', 'group')

        # Removing M2M table for field meta on 'Resource'
        db.delete_table('im_resource_meta')

        # Adding unique constraint on 'Resource', fields ['name']
        db.create_unique('im_resource', ['name'])

        # Deleting field 'ProjectResourceGrant.member_import_limit'
        db.delete_column('im_projectresourcegrant', 'member_import_limit')

        # Deleting field 'ProjectResourceGrant.project_export_limit'
        db.delete_column('im_projectresourcegrant', 'project_export_limit')

        # Deleting field 'ProjectResourceGrant.project_import_limit'
        db.delete_column('im_projectresourcegrant', 'project_import_limit')

        # Deleting field 'ProjectResourceGrant.member_export_limit'
        db.delete_column('im_projectresourcegrant', 'member_export_limit')

        # Changing field 'ProjectResourceGrant.project_capacity'
        db.alter_column('im_projectresourcegrant', 'project_capacity', self.gf('snf_django.lib.db.fields.IntDecimalField')(null=True, max_digits=38, decimal_places=0))

    def backwards(self, orm):

        # Removing unique constraint on 'Resource', fields ['name']
        db.delete_unique('im_resource', ['name'])

        # Adding model 'ResourceMetadata'
        db.create_table('im_resourcemetadata', (
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, db_index=True)),
        ))
        db.send_create_signal('im', ['ResourceMetadata'])

        # Adding field 'AstakosUserQuota.import_limit'
        db.add_column('im_astakosuserquota', 'import_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'AstakosUserQuota.export_limit'
        db.add_column('im_astakosuserquota', 'export_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'AstakosUserQuota.quantity'
        db.add_column('im_astakosuserquota', 'quantity', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=0, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'Service.order'
        db.add_column('im_service', 'order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0), keep_default=False)

        # Adding field 'Service.icon'
        db.add_column('im_service', 'icon', self.gf('django.db.models.fields.FilePathField')(default='', max_length=100, blank=True), keep_default=False)

        # Deleting field 'Service.api_url'
        db.delete_column('im_service', 'api_url')

        # Changing field 'Service.url'
        db.alter_column('im_service', 'url', self.gf('django.db.models.fields.FilePathField')(default='', max_length=100))

        # Adding field 'Project.is_active'
        db.add_column('im_project', 'is_active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True), keep_default=False)

        # Adding field 'Project.is_modified'
        db.add_column('im_project', 'is_modified', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True), keep_default=False)

        # Adding field 'ProjectMembership.is_active'
        db.add_column('im_projectmembership', 'is_active', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True), keep_default=False)

        # Adding field 'ProjectMembership.pending_application'
        db.add_column('im_projectmembership', 'pending_application', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pending_memberships', null=True, to=orm['im.ProjectApplication']), keep_default=False)

        # Adding field 'ProjectMembership.pending_serial'
        db.add_column('im_projectmembership', 'pending_serial', self.gf('django.db.models.fields.BigIntegerField')(null=True, db_index=True), keep_default=False)

        # Adding field 'ProjectMembership.application'
        db.add_column('im_projectmembership', 'application', self.gf('django.db.models.fields.related.ForeignKey')(related_name='memberships', null=True, to=orm['im.ProjectApplication']), keep_default=False)

        # Adding field 'ProjectMembership.is_pending'
        db.add_column('im_projectmembership', 'is_pending', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True), keep_default=False)

        # Adding field 'Resource.group'
        db.add_column('im_resource', 'group', self.gf('django.db.models.fields.CharField')(max_length=255, null=True), keep_default=False)

        # Adding M2M table for field meta on 'Resource'
        db.create_table('im_resource_meta', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resource', models.ForeignKey(orm['im.resource'], null=False)),
            ('resourcemetadata', models.ForeignKey(orm['im.resourcemetadata'], null=False))
        ))
        db.create_unique('im_resource_meta', ['resource_id', 'resourcemetadata_id'])

        # Adding unique constraint on 'Resource', fields ['name', 'service']
        db.create_unique('im_resource', ['name', 'service_id'])

        # Adding field 'ProjectResourceGrant.member_import_limit'
        db.add_column('im_projectresourcegrant', 'member_import_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'ProjectResourceGrant.project_export_limit'
        db.add_column('im_projectresourcegrant', 'project_export_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'ProjectResourceGrant.project_import_limit'
        db.add_column('im_projectresourcegrant', 'project_import_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Adding field 'ProjectResourceGrant.member_export_limit'
        db.add_column('im_projectresourcegrant', 'member_export_limit', self.gf('snf_django.lib.db.fields.IntDecimalField')(default=100000000000000000000000000000000L, max_digits=38, decimal_places=0), keep_default=False)

        # Changing field 'ProjectResourceGrant.project_capacity'
        db.alter_column('im_projectresourcegrant', 'project_capacity', self.gf('snf_django.lib.db.fields.IntDecimalField')(max_digits=38, decimal_places=0))

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'im.additionalmail': {
            'Meta': {'object_name': 'AdditionalMail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.AstakosUser']"})
        },
        'im.approvalterms': {
            'Meta': {'object_name': 'ApprovalTerms'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'im.astakosuser': {
            'Meta': {'object_name': 'AstakosUser', '_ormbases': ['auth.User']},
            'activation_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'affiliation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'auth_token': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'auth_token_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'auth_token_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_signed_terms': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'disturbed_quota': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_credits': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_signed_terms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'invitations': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'is_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'policy': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['im.Resource']", 'null': 'True', 'through': "orm['im.AstakosUserQuota']", 'symmetrical': 'False'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'third_party_identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True'})
        },
        'im.astakosuserauthprovider': {
            'Meta': {'ordering': "('module', 'created')", 'unique_together': "(('identifier', 'module', 'user'),)", 'object_name': 'AstakosUserAuthProvider'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'affiliation': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'auth_backend': ('django.db.models.fields.CharField', [], {'default': "'astakos'", 'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'info_data': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'module': ('django.db.models.fields.CharField', [], {'default': "'local'", 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_providers'", 'to': "orm['im.AstakosUser']"})
        },
        'im.astakosuserquota': {
            'Meta': {'unique_together': "(('resource', 'user'),)", 'object_name': 'AstakosUserQuota'},
            'capacity': ('snf_django.lib.db.fields.IntDecimalField', [], {'max_digits': '38', 'decimal_places': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.Resource']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.AstakosUser']"})
        },
        'im.authproviderpolicyprofile': {
            'Meta': {'ordering': "['priority']", 'object_name': 'AuthProviderPolicyProfile'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'authpolicy_profiles'", 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'policy_add': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_automoderate': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_create': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_limit': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'policy_login': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_remove': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_required': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'policy_switch': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'authpolicy_profiles'", 'symmetrical': 'False', 'to': "orm['im.AstakosUser']"})
        },
        'im.chain': {
            'Meta': {'object_name': 'Chain'},
            'chain': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'im.emailchange': {
            'Meta': {'object_name': 'EmailChange'},
            'activation_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_email_address': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'requested_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'emailchanges'", 'unique': 'True', 'to': "orm['im.AstakosUser']"})
        },
        'im.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'code': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'consumed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_sent'", 'null': 'True', 'to': "orm['im.AstakosUser']"}),
            'is_consumed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'realname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'im.pendingthirdpartyuser': {
            'Meta': {'unique_together': "(('provider', 'third_party_identifier'),)", 'object_name': 'PendingThirdPartyUser'},
            'affiliation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'third_party_identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'im.project': {
            'Meta': {'object_name': 'Project'},
            'application': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'project'", 'unique': 'True', 'to': "orm['im.ProjectApplication']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deactivation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'deactivation_reason': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'chained_project'", 'unique': 'True', 'primary_key': 'True', 'db_column': "'id'", 'to': "orm['im.Chain']"}),
            'last_approval_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['im.AstakosUser']", 'through': "orm['im.ProjectMembership']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'})
        },
        'im.projectapplication': {
            'Meta': {'unique_together': "(('chain', 'id'),)", 'object_name': 'ProjectApplication'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects_applied'", 'to': "orm['im.AstakosUser']"}),
            'chain': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'chained_apps'", 'db_column': "'chain'", 'to': "orm['im.Chain']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'limit_on_members_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'member_join_policy': ('django.db.models.fields.IntegerField', [], {}),
            'member_leave_policy': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects_owned'", 'to': "orm['im.AstakosUser']"}),
            'precursor_application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.ProjectApplication']", 'null': 'True', 'blank': 'True'}),
            'resource_grants': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['im.Resource']", 'null': 'True', 'through': "orm['im.ProjectResourceGrant']", 'blank': 'True'}),
            'response': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'response_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'im.projectmembership': {
            'Meta': {'unique_together': "(('person', 'project'),)", 'object_name': 'ProjectMembership'},
            'acceptance_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'leave_request_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.AstakosUser']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.Project']"}),
            'request_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'im.projectmembershiphistory': {
            'Meta': {'object_name': 'ProjectMembershipHistory'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.BigIntegerField', [], {}),
            'project': ('django.db.models.fields.BigIntegerField', [], {}),
            'reason': ('django.db.models.fields.IntegerField', [], {}),
            'serial': ('django.db.models.fields.BigIntegerField', [], {})
        },
        'im.projectresourcegrant': {
            'Meta': {'unique_together': "(('resource', 'project_application'),)", 'object_name': 'ProjectResourceGrant'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member_capacity': ('snf_django.lib.db.fields.IntDecimalField', [], {'default': '0', 'max_digits': '38', 'decimal_places': '0'}),
            'project_application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.ProjectApplication']", 'null': 'True'}),
            'project_capacity': ('snf_django.lib.db.fields.IntDecimalField', [], {'null': 'True', 'max_digits': '38', 'decimal_places': '0'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.Resource']"})
        },
        'im.resource': {
            'Meta': {'object_name': 'Resource'},
            'desc': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.Service']"}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'uplimit': ('snf_django.lib.db.fields.IntDecimalField', [], {'default': '0', 'max_digits': '38', 'decimal_places': '0'})
        },
        'im.serial': {
            'Meta': {'object_name': 'Serial'},
            'serial': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'im.service': {
            'Meta': {'object_name': 'Service'},
            'api_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'auth_token': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'auth_token_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'auth_token_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'im.sessioncatalog': {
            'Meta': {'object_name': 'SessionCatalog'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sessions'", 'null': 'True', 'to': "orm['im.AstakosUser']"})
        },
        'im.usersetting': {
            'Meta': {'unique_together': "(('user', 'setting'),)", 'object_name': 'UserSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'setting': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['im.AstakosUser']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['im']
