from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required

@login_required
def download_missing_data(request):
    """ Serve the missing data CSV file for download """
    missing_data_rows = request.session.get('missing_data', [])
    if not missing_data_rows:
        return HttpResponse("No missing data available.", content_type="text/plain")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="missing_data.csv"'

    writer = csv.DictWriter(response, fieldnames=missing_data_rows[0].keys())
    writer.writeheader()
    writer.writerows(missing_data_rows)

    return response