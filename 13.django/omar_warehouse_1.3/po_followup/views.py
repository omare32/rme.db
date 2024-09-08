from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from .forms import PoFollowupForm 

def po_followup_report(request):
    if request.method == 'POST':
        form = PoFollowupForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']

            with connection.cursor() as cursor:
                # Query for highest and lowest unit prices
                query = """
                    SELECT TOP 1
                        unit_price, approved_date, vendor, project_name
                    FROM 
                        po_followup
                    WHERE 
                        LOWER(description) = LOWER(%s)
                    ORDER BY 
                        unit_price DESC;

                    SELECT TOP 1
                        unit_price, approved_date, vendor, project_name
                    FROM 
                        po_followup
                    WHERE 
                        LOWER(description) = LOWER(%s)
                    ORDER BY 
                        unit_price ASC;
                """
                params = [description, description]

                try:
                    cursor.execute(query, params)
                    highest_price_result = cursor.fetchone()
                    lowest_price_result = cursor.fetchone()

                except Exception as e:
                    print(f"Error executing query: {e}")
                    highest_price_result = None
                    lowest_price_result = None

            context = {
                'description': description,
                'highest_price': highest_price_result,
                'lowest_price': lowest_price_result,
            }

            return render(request, 'po_followup/report.html', context)

    else:
        form = PoFollowupForm()

    return render(request, 'po_followup/report.html', {'form': form})

def get_matching_descriptions(request):
    if request.method == 'GET':
        search_term = request.GET.get('term', '') 

        with connection.cursor() as cursor:
            # Query for descriptions containing the search term (case-insensitive)
            query = """
                SELECT DISTINCT description 
                FROM po_followup
                WHERE LOWER(description) LIKE LOWER(%s);
            """
            params = ['%' + search_term + '%']

            try:
                cursor.execute(query, params)
                results = cursor.fetchall()
                descriptions = [row[0] for row in results]

            except Exception as e:
                print(f"Error executing query: {e}")
                descriptions = []

        return JsonResponse(descriptions, safe=False)  # Return only the JsonResponse