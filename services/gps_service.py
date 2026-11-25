import asyncio
import inspect
import flet as ft
try:
    import flet_geolocator as ftg
except ImportError:
    ftg = None

class GPSService:
    def __init__(self, page: ft.Page):
        self.page = page
        self._geo = None
        if ftg is not None:
            self._geo = ftg.Geolocator()
            try:
                if hasattr(self.page, 'services') and self._geo not in self.page.services:
                    self.page.services.append(self._geo)
                elif hasattr(self.page, 'overlay') and self._geo not in self.page.overlay:
                    self.page.overlay.append(self._geo)
            except Exception:
                pass

    async def _llamar(self, fn, *args, **kwargs):
        res = fn(*args, **kwargs)
        return await res if inspect.iscoroutine(res) else res

    async def obtener_posicion_actual(self) -> dict:
        if self._geo is None:
            raise RuntimeError('Modulo GPS no disponible.')
        try:
            permiso = await self._llamar(self._geo.get_permission_status)
            if 'denied' in str(permiso).lower() or 'unable' in str(permiso).lower():
                await self._llamar(self._geo.request_permission)
        except Exception:
            try:
                await self._llamar(self._geo.request_permission)
            except Exception:
                pass
        pos = None
        try:
            pos = await asyncio.wait_for(self._llamar(self._geo.get_current_position), timeout=10.0)
        except Exception:
            if hasattr(self._geo, 'get_last_known_position'):
                try:
                    pos = await self._llamar(self._geo.get_last_known_position)
                except Exception:
                    pos = None
        if pos is None:
            raise RuntimeError('Sin senal GPS fija. Sal a cielo abierto.')
        return {'lat': round(float(pos.latitude), 6), 'lon': round(float(pos.longitude), 6), 'precision': round(float(getattr(pos, 'accuracy', 0.0) or 0.0), 1)}
