# Generated by Django 3.2.25 on 2024-09-04 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
            ],
            options={
                'db_table': 'auth_group',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthGroupPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_group_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('codename', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'auth_permission',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField()),
                ('username', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=254)),
                ('is_staff', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('date_joined', models.DateTimeField()),
            ],
            options={
                'db_table': 'auth_user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserGroups',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_groups',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserUserPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_user_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CostDist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trs_id', models.FloatField(blank=True, null=True)),
                ('transaction_source', models.CharField(blank=True, max_length=255, null=True)),
                ('project_no', models.FloatField(blank=True, null=True)),
                ('project_name', models.CharField(blank=True, max_length=255, null=True)),
                ('project_zone', models.CharField(blank=True, max_length=255, null=True)),
                ('task_no', models.CharField(blank=True, max_length=255, null=True)),
                ('task_name', models.CharField(blank=True, max_length=255, null=True)),
                ('top_task_no', models.FloatField(blank=True, null=True)),
                ('top_task_name', models.CharField(blank=True, max_length=255, null=True)),
                ('po_no', models.CharField(blank=True, max_length=255, null=True)),
                ('gl_date', models.DateTimeField(blank=True, null=True)),
                ('expenditure_type', models.CharField(blank=True, max_length=255, null=True)),
                ('project_location', models.CharField(blank=True, max_length=255, null=True)),
                ('project_floor', models.CharField(blank=True, max_length=255, null=True)),
                ('project_area', models.CharField(blank=True, max_length=255, null=True)),
                ('expenditure_category', models.CharField(blank=True, max_length=255, null=True)),
                ('expend_org', models.CharField(blank=True, max_length=255, null=True)),
                ('amount', models.FloatField(blank=True, null=True)),
                ('line_no', models.FloatField(blank=True, null=True)),
                ('line_desc', models.CharField(blank=True, max_length=255, null=True)),
                ('inv_no', models.CharField(blank=True, max_length=255, null=True)),
                ('unit', models.CharField(blank=True, max_length=255, null=True)),
                ('qty', models.FloatField(blank=True, null=True)),
                ('ipc_no', models.FloatField(blank=True, null=True)),
                ('supplier_no', models.CharField(blank=True, max_length=255, null=True)),
                ('supplier_name', models.CharField(blank=True, max_length=255, null=True)),
                ('supplier_site', models.CharField(blank=True, max_length=255, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('inventory_item', models.CharField(blank=True, max_length=255, null=True)),
                ('owner', models.CharField(blank=True, max_length=255, null=True)),
                ('distributions_status', models.CharField(blank=True, max_length=255, null=True)),
                ('distributions_date', models.DateTimeField(blank=True, null=True)),
                ('distributions_details', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'cost_dist',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoAdminLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField()),
                ('object_id', models.TextField(blank=True, null=True)),
                ('object_repr', models.CharField(max_length=200)),
                ('action_flag', models.SmallIntegerField()),
                ('change_message', models.TextField()),
            ],
            options={
                'db_table': 'django_admin_log',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoContentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'django_content_type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_migrations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoSession',
            fields=[
                ('session_key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('session_data', models.TextField()),
                ('expire_date', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_session',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MatMov',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trx_id', models.FloatField(blank=True, null=True)),
                ('item_code', models.CharField(blank=True, max_length=255, null=True)),
                ('item_desc', models.CharField(blank=True, max_length=255, null=True)),
                ('unit', models.CharField(blank=True, max_length=255, null=True)),
                ('from_field', models.CharField(blank=True, db_column='from', max_length=255, null=True)),
                ('to', models.CharField(blank=True, max_length=255, null=True)),
                ('project_name', models.CharField(blank=True, max_length=255, null=True)),
                ('project_no', models.FloatField(blank=True, null=True)),
                ('exp_id', models.CharField(blank=True, max_length=255, null=True)),
                ('task_no', models.CharField(blank=True, max_length=255, null=True)),
                ('exp_type', models.CharField(blank=True, max_length=255, null=True)),
                ('material_type', models.CharField(blank=True, max_length=255, null=True)),
                ('supplier_name', models.CharField(blank=True, max_length=255, null=True)),
                ('supplier_no', models.FloatField(blank=True, null=True)),
                ('trx_type', models.CharField(blank=True, max_length=255, null=True)),
                ('move_order_no', models.CharField(blank=True, max_length=255, null=True)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('rate', models.FloatField(blank=True, null=True)),
                ('qty', models.FloatField(blank=True, null=True)),
                ('po_no', models.FloatField(blank=True, null=True)),
                ('amount', models.FloatField(blank=True, null=True)),
                ('project_area', models.CharField(blank=True, max_length=255, null=True)),
                ('issued_type', models.CharField(blank=True, max_length=255, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'mat_mov',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Sysdiagrams',
            fields=[
                ('name', models.CharField(max_length=128)),
                ('principal_id', models.IntegerField()),
                ('diagram_id', models.AutoField(primary_key=True, serialize=False)),
                ('version', models.IntegerField(blank=True, null=True)),
                ('definition', models.BinaryField(blank=True, max_length='max', null=True)),
            ],
            options={
                'db_table': 'sysdiagrams',
                'managed': False,
            },
        ),
    ]
