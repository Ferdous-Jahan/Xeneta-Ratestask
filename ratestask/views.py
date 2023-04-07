from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ratestask.models import Regions, Ports, Prices
from ratestask.serializers import RegionsSerializer, PortsSerializer, PricesSerializer
from rest_framework import status
from datetime import datetime, timedelta

@csrf_exempt
@api_view(['GET'])
def average_price_list(request):
    """
    List average prices for a date range in particular geographic groups of ports
    """

    try:
        date_from_string = request.GET.get('date_from') if 'date_from' in request.GET and len(request.GET.get('date_from')) > 0 else None
        date_to_string = request.GET.get('date_to') if 'date_to' in request.GET and len(request.GET.get('date_to')) > 0 else None
        origin = request.GET.get('origin') if 'origin' in request.GET and len(request.GET.get('origin')) > 0 else None
        destination = request.GET.get('destination') if 'destination' in request.GET and len(request.GET.get('destination')) > 0 else None

        if date_from_string is not None and date_to_string is not None and origin is not None and destination is not None:
            # Get regions from query params
            origin_regions = Regions.objects.raw("SELECT * FROM regions WHERE slug = %s OR parent_slug=%s", [origin,origin])
            destination_regions = Regions.objects.raw("SELECT * FROM regions WHERE slug = %s OR parent_slug=%s", [destination,destination])

            origin_regions_serializer = RegionsSerializer(origin_regions, many=True)
            destination_regions_serializer = RegionsSerializer(destination_regions, many=True)

            # Get origin ports that falls under the regions from the query param
            if len(origin_regions_serializer.data) > 0:
                origin_ports_list = get_port_list(origin_regions_serializer)
            else:
                # Or if direct port code was available get the port
                origin_ports_list = get_port(origin)
                
            # Same for destination ports
            if len(destination_regions_serializer.data) > 0:
                destination_ports_list = get_port_list(destination_regions_serializer)
            else:
                destination_ports_list = get_port(destination)

            # Get prices that matches the query params criteria
            if len(destination_ports_list) > 0 and len(origin_ports_list) > 0:
                prices = get_prices(origin_ports_list, destination_ports_list, date_from_string, date_to_string)
            else:
                # otherwise raise exception if the origin or destination port or region name does not exist in database
                raise Exception("destination or origin port does not exist")

            # Make a date list in YYYY-MM-DD format for (date_from - date_to)
            day_from = datetime.strptime(date_from_string, '%Y-%m-%d')
            day_to = datetime.strptime(date_to_string, '%Y-%m-%d')
            
            date_list = [day_from + timedelta(days=x) for x in range((day_to - day_from).days+1)]
            date_list = [d.strftime('%Y-%m-%d') for d in date_list]

            days_available = []
            for price in prices:
                days_available.append(price['day'])

            # separate list for days that will have null average_price and valid average_price
            null_values = []
            available_price_values = []
            for date in date_list:
                if days_available.count(date) >=3:
                    for price in prices:
                        if date == price['day']:
                            available_price_values.append({'day': date, 'average_price': price['price']})
                else:
                    null_values.append({'day': date, 'average_price': None})
            
            averages = {}
            counts = {}

            # Create list of dicts with valid average_price days
            for item in available_price_values:
                day = item['day']
                price = item['average_price']
                
                if day in averages:
                    averages[day] += price
                    counts[day] += 1
                else:
                    averages[day] = price
                    counts[day] = 1
                    
            days_with_average_price = [{'day': day, 'average_price': averages[day]/counts[day]} for day in averages]

            new_dict = {item['day']: item['average_price'] for item in null_values}

            for item in days_with_average_price:
                day = item['day']
                if day in new_dict:
                    item['average_price'] = new_dict[day]

            # Combine the two lists
            combined_list = days_with_average_price + null_values

            # Sort the combined list by the day key
            sorted_list = sorted(combined_list, key=lambda x: x['day'])
            return Response( sorted_list,  status=status.HTTP_200_OK)
        else:
            # response for requests with missing param(s)
            return Response( {'message': 'One or more parameters are missing'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        data = {'error': str(e)}
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_port_list(regions_serializer):
    region_list = []
    for region in regions_serializer.data:
        region_list.append(region['slug'])
    ports = Ports.objects.raw('SELECT * FROM ports WHERE parent_slug IN {};'.format(tuple(region_list)))
    ports_serializer = PortsSerializer(ports, many=True)
    ports_list = []
    for port in ports_serializer.data:
        ports_list.append(port['code'])
    return ports_list

def get_port(port):
    ports_list = []
    query_result_port = Ports.objects.raw('SELECT * FROM ports WHERE code= %s', [port])
    for port in query_result_port:
        ports_list.append(port.code)
    return ports_list

def get_prices(origin_ports_list, destination_ports_list, date_from, date_to):
    if len(origin_ports_list) > 1 and len(destination_ports_list) > 1:
        prices = Prices.objects.raw("SELECT * FROM prices WHERE orig_code in {origin} AND dest_code in {destination} AND day >= '{date_from}' AND day <= '{date_to}' ORDER BY id ASC".format(origin=tuple(origin_ports_list),destination=tuple(destination_ports_list), date_from=date_from,date_to=date_to))
    elif len(origin_ports_list) > 1 and len(destination_ports_list) <= 1:
        prices = Prices.objects.raw("SELECT * FROM prices WHERE orig_code in {origin} AND dest_code in ('{destination}') AND day >= '{date_from}' AND day <= '{date_to}' ORDER BY id ASC".format(origin=tuple(origin_ports_list),destination=destination_ports_list[0], date_from=date_from,date_to=date_to))
    elif len(origin_ports_list) > 1 and len(destination_ports_list) <= 1:
        prices = Prices.objects.raw("SELECT * FROM prices WHERE orig_code in ('{origin}') AND dest_code in {destination} AND day >= '{date_from}' AND day <= '{date_to}' ORDER BY id ASC".format(origin=origin_ports_list[0],destination=tuple(destination_ports_list), date_from=date_from,date_to=date_to))
    else:
        prices = Prices.objects.raw("SELECT * FROM prices WHERE orig_code in ('{origin}') AND dest_code in ('{destination}') AND day >= '{date_from}' AND day <= '{date_to}' ORDER BY id ASC".format(origin=origin_ports_list[0],destination=destination_ports_list[0], date_from=date_from,date_to=date_to))

    prices_serializer = PricesSerializer(prices, many=True)
    return prices_serializer.data