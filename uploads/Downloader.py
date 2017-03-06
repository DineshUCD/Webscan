#Send large files through Django
import os, tempfile, zipfile, json

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper

from scans.models import Scan
from scans.Zipper import ZipArchive

import os, mimetypes, logging, urlparse

logger = logging.getLogger('scarab')


def send_file(request):
    """
    Send a file through Django without loading the whole file into memory at once.
    The FileWrapper will turn the file object into an iterator for chunks of 8KB.
    """
    if not request.method == 'GET':
        return JsonResponse(data={'message': 'View Does Not Exist.'}, status=404)

    __file__ = request.GET.get('resources[]', None)
    scan_pk  = request.GET.get('scan', None)

    #Find __file__ using scan_pk
    if not Scan.objects.filter(pk=scan_pk, user_profile__id=request.user.userprofile.id).exists():
        return JsonResponse(data={'message': 'Suspicious Operation'}, status=400)

    try:
        archive = ZipArchive(scan=scan_pk)
        __file__ = archive.unzip(list(__file__))
    except IndexError as err:
        return JsonResponse(data={'message': 'Resource Not Found'}, status=400)
   
    filename = os.path.basename(__file__) #Select your file here.
    chunksize = 8192
    wrapper = FileWrapper(open(__file__), chunksize)
    response = StreamingHttpResponse(wrapper, content_type=mimetypes.guess_type(__file__)[0])
    response['Content-Length'] = os.path.getsize(__file__)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    archive.close()
    return response

#workhorse class to download
def send_zipfile(request):
    """
    Create a  ZIP file on disk and transmit it in chunks of 8KB
    without loading the whole file into memory. tempfiles are stored in /tmp.
    A similar approach can be used for large dynamic PDF files
    """
    if not request.method == 'GET':
        return JsonResponse(data={'message': 'View Does Not Exist.'}, status=404)
    # Get the Query URL
    url = request.GET.urlencode()
    # Parse the query string 
    queries = urlparse.parse_qs(url) 

    try:
        scan_pk = int(queries['scan'][0])
        files   = queries['resources[]']
    except (TypeError, KeyError) as err:
        return JsonResponse(data={'message': 'Invalid Resource Request'}, status=400)
    else: 
       for index in range(len(files)):
           files[index] = files[index].encode('utf-8')

    if not Scan.objects.filter(pk=scan_pk, user_profile__id=request.user.userprofile.id).exists():
        return JsonResponse(data={'message': 'Suspicious Operation'}, status=400)

    #Find files using scan_pk
    zipper = ZipArchive(scan=scan_pk)  
    files = zipper.unzip(files)

    if not files:
        return JsonResponse(data={'message': 'Invalid Resource Request'}, status=400)
   
    try:
        #<fdopen>, indicating an open file handle, but no corresponding directory entry
      
        temp = tempfile.TemporaryFile()
        archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
        for filename in files:
            archive.write(filename, '%s' % os.path.basename(filename))
        archive.close()   
        content_length = temp.tell()
        temp.seek(0)
        wrapper = FileWrapper(temp)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=results.zip'
        response['Content-Length'] = content_length
    except (TypeError, IOError) as err:
        return JsonResponse({'message': 'Suspicious Operation'}, status=400)
    finally:
        zipper.close()
    return response
