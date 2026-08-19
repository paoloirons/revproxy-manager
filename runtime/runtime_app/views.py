from django.http import JsonResponse, HttpResponseNotFound, HttpResponseForbidden
from revproxy.views import ProxyView
from .config import routes, route_acls, effective_ip, in_any

def health(request): return JsonResponse({'ok':True})

class DynamicProxyView(ProxyView):
 add_x_forwarded=True
 def dispatch(self, request, *args, **kwargs):
  request_path='/' + kwargs.get('path','').lstrip('/')
  selected=None
  for r in routes():
   prefix=r['path_prefix']
   if request_path==prefix.rstrip('/') or request_path.startswith(prefix):
    selected=r;break
  if not selected:return HttpResponseNotFound('No enabled proxy route matches this path')
  allowed=route_acls(selected['id'])
  if allowed:
   peer=request.META.get('REMOTE_ADDR','')
   client=effective_ip(peer,request.META.get('HTTP_X_FORWARDED_FOR',''))
   if not in_any(client,allowed):return HttpResponseForbidden('Source IP is not allowed for this route')
  prefix=selected['path_prefix']
  remainder=request_path[len(prefix.rstrip('/')):].lstrip('/')
  self.upstream=selected['upstream']
  kwargs['path']=remainder
  return super().dispatch(request,*args,**kwargs)
