from django.db import models

class Ports(models.Model):
    code = models.TextField(primary_key=True)
    name = models.TextField()
    parent_slug = models.ForeignKey('Regions', models.DO_NOTHING, db_column='parent_slug')

    class Meta:
        db_table = 'ports'


class Prices(models.Model):
    orig_code = models.ForeignKey(Ports, models.DO_NOTHING, db_column='orig_code', related_name="origin_port_code", default="some")
    dest_code = models.ForeignKey(Ports, models.DO_NOTHING, db_column='dest_code', related_name="destination_port_code", default="some")
    day = models.DateField()
    price = models.IntegerField()

    class Meta:
        db_table = 'prices'


class Regions(models.Model):
    slug = models.TextField(primary_key=True)
    name = models.TextField()
    parent_slug = models.ForeignKey('self', models.DO_NOTHING, db_column='parent_slug', blank=True, null=True)

    class Meta:
        db_table = 'regions'