from rest_framework import serializers
from ratestask.models import Ports, Prices, Regions

class RegionsSerializer(serializers.ModelSerializer):
    parent_slug = serializers.SerializerMethodField()

    class Meta:
        model = Regions
        fields = '__all__'
    
    def get_parent_slug(self, obj):
        if obj.parent_slug is not None:
            return RegionsSerializer(obj.parent_slug).data
        else:
            return None

class PortsSerializer(serializers.ModelSerializer):
    parent_slug = RegionsSerializer(read_only=True)

    class Meta:
        model = Ports
        fields = '__all__'

class PricesSerializer(serializers.ModelSerializer):
    #orig_code = PortsSerializer(read_only=True)
    #dest_code = PortsSerializer(read_only=True)

    class Meta:
        model = Prices
        fields = ['day','price']
