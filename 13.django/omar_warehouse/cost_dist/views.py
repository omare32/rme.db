from django.shortcuts import render
from django.db import connection
from .forms import CostDistForm
from .utils import get_distinct_project_names 

def cost_dist_report(request):
    if request.method == 'POST':
        form = CostDistForm(request.POST)
        if form.is_valid():
            project_identifier_type = form.cleaned_data['project_identifier_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            show_details = form.cleaned_data['show_details']

            with connection.cursor() as cursor:
                if project_identifier_type == 'project_no':
                    project_identifier = form.cleaned_data['project_identifier']
                    query = f"""
                        SELECT 
                            project_no, 
                            project_name, 
                            SUM(amount) AS total_cost
                        FROM 
                            cost_dist
                        WHERE 
                            project_no = %s 
                            {f'AND gl_date BETWEEN %s AND %s' if start_date and end_date else ''} 
                        GROUP BY 
                            project_no, project_name;
                    """

                    # Adjust params based on whether dates are provided
                    if start_date and end_date:
                        params = [project_identifier, start_date, end_date]
                    else:
                        params = [project_identifier]

                else:  # project_identifier_type == 'project_name'
                    project_name = form.cleaned_data['project_name']
                    query = f"""
                        SELECT 
                            project_no, 
                            project_name, 
                            SUM(amount) AS total_cost
                        FROM 
                            cost_dist
                        WHERE 
                            LOWER(project_name) = LOWER(%s) 
                            {'AND gl_date BETWEEN %s AND %s' if start_date and end_date else ''} 
                        GROUP BY 
                            project_no, project_name;
                    """

                    # Adjust params based on whether dates are provided
                    if start_date and end_date:
                        params = [project_name, start_date, end_date]
                    else:
                        params = [project_name]

                cursor.execute(query, params)
                results = cursor.fetchall()

            if show_details:
                context = {'results': results}
            else:
                total_amount = sum(row[2] for row in results)
                
                # Format the total_amount with commas
                formatted_total_amount = "{:,.2f}".format(total_amount)  

                context = {'total_amount': formatted_total_amount}  # Pass the formatted amount to the template

            return render(request, 'cost_dist/report.html', context)
    else:
        form = CostDistForm()

    return render(request, 'cost_dist/report.html', {'form': form})