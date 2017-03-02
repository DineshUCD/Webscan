#Send large files through Django
import os, tempfile, zipfile, json

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper

from scans.models import Scan
from scans.Zipper import ZipArchive

import os, mimetypes, logging

logger = logging.getLogger('scarab')

#Do not verify UserProfile here. Alllows for Admin use.
def extract_from_archival(resources, scan_pk):
    if not resources or not scan_pk:
        logger.error("The requested resource does not support one or more of the given parameters.")
        return None

    #flatten the list of filepaths
    try:
        container = list()
        for resource in resources:
            if isinstance(resource, list):
                container.extend(resource)
            else:
                container.append(resource)
    except (MemoryError, RuntimeError) as err:
        logger.error("Unexpected internal server error: {0}".format(err))
        return None

    archive = ZipArchive(scan=scan_pk)
    output = archive.unzip(container)

    if not output:
        logger.error('Resource Not Found')
    
    return output

def send_file(request):
    """
    Send a file through Django without loading the whole file into memory at once.
    The FileWrapper will turn the file object into an iterator for chunks of 8KB.
    """
    if not request.method == 'GET':
        return JsonResponse(data={'message': 'View Does Not Exist.'}, status=404)

    __file__ = request.GET.get('resources', None)
    scan_pk  = request.GET.get('scan', None)

    #Find __file__ using scan_pk
    if not Scan.objects.filter(pk=scan_pk, user_profile__id=request.user.userprofile.id).exists():
        return JsonResponse(data={'message': 'Suspicious Operation'}, status=400)

    try:
        __file__ = extract_from_archival(__file__, scan_pk)[0]
    except IndexError as err:
        return JsonResponse(data={'message': 'Resource Not Found'}, status=400)

    filename = os.path.basename(__file__) #Select your file here.
    chunksize = 8192
    wrapper = FileWrapper(open(__file__), chunksize)
    response = StreamingHttpResponse(wrapper, content_type=mimetype.guess_type(__file__)[0])
    response['Content-Length'] = os.path.getsize(__file__)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
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

    files = request.GET.get('resources', None)
    scan_pk = request.GET.get('scan', None)

    if not Scan.objects.filter(pk=scan_pk, user_profile__id=request.user.userprofile.id).exists():
        return JsonResponse(data={'message': 'Suspicious Operation'}, status=400)

    #Find files using scan_pk
    files = extract_from_archival(files, scan_pk)

    if not files:
        return JsonResponse(data={'message': 'Invalid Resource Request'}, status=400)
   
    #<fdopen>, indicating an open file handle, but no corresponding directory entry
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

    try:
        for filename in files:
            archive.write(filename, '%s' % os.path.basename(filename))
        wrapper = FileWrapper(temp)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=results.zip'
        response['Content-Length'] = temp.tell()
        temp.seek(0)
    except (TypeError, IOError) as err:
        return JsonResponse({'message': 'Suspicious Operation'}, status=400)
    finally:
        archive.close()

    return response
