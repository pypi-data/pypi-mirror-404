import os
import sys
import pwd
import asyncio
import datetime
import subprocess
from typing import Set, Tuple, Optional, Iterable, Union, Callable, List, Coroutine, Any, cast
from GNServer import GNServer as _App, AsyncClient, GNRequest, GNResponse, Url, responses, GNServer as _GNServer
from KeyisBTools.models.serialization import serialize
from KeyisBTools.bytes.transformation import userFriendly
from pathlib import Path
import json

uid = int(os.environ.get("SUDO_UID", os.getuid()))
home = pwd.getpwuid(uid).pw_dir
# def restart_as_root():
#     if os.geteuid() != 0: # type: ignore
#         os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
# restart_as_root()

from ._f import _kill_process_by_port, is_port_in_use, trim_old_files, _domain_from_web2_to_web5, _domain_from_web5_to_web2, AsyncLogWriter
from KeyisBTools.cryptography.sign import s1

try:

    import os
    import pwd

    _username = pwd.getpwuid(os.getuid()).pw_name # type: ignore
    PID_FILE = f"{home}/GW/GN/vmhost/data/server.pid"
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
except Exception as e:
    print(f'WORNING: can\'t write pid file -> {e}')
    pass


class App():
    def __init__(self):
        self._app = _App()

        self._servers = {}


        self._default_venv_path = None
        self._default_TLS_paths = None
        self._log_dir_path: Optional[str] = None


        self.__add_routes()

        self.tgbot: Optional[Tuple[str, List[int], Any]] = None

        self._log_max_files = 10

        self._cloud_host_domain: Optional[str] = None

        self._startType = None

    def setCloudHostDomain(self, domain: str):
        self._cloud_host_domain = domain

    def runGNServerVMHostEnvironment(self, run: bool = True):
        self._startType = 'gn-server-vm-host-environment'

        base = Path(f'{home}/GW/GN')
        servers_config_dir = base / 'config/servers'

        vm = None

        for i in os.listdir(servers_config_dir):
            p = Path(servers_config_dir) / i
            if p.is_dir():
                domain = i

                p_config = {}
                if os.path.exists(str(p / 'hostconfig.json')):
                    p_config = json.load(open(str(p / 'hostconfig.json')))

                _repo_name = p_config.get('start_repo', None)
                if _repo_name is None:
                    _path_repo = base / 'servers' / domain
                    if not os.path.exists(str(_path_repo)):
                        _path_repo = base / 'servers' / _domain_from_web5_to_web2(domain)
                else:
                    _path_repo = base / 'servers' / _repo_name

                start = p_config.get('start_file', None)
                if os.path.exists(str(_path_repo / 'server.py')):
                    start = str(_path_repo / 'server.py')

                if os.path.exists(str(_path_repo / 'start.sh')):
                    start = str(_path_repo / 'start.sh')

                s_config = {}
                if os.path.exists(str(p / 'config.json')):
                    s_config = json.load(open(str(p / 'config.json')))

                if start is None:
                    raise ValueError(f"Server start file not found for domain: {domain}")
                
                self.addServerStartFile(
                    domain=_domain_from_web2_to_web5(domain),
                    file_path=start,
                    port=p_config.get('port', 40002),
                    start_when_run=True,
                    venv_path=p_config.get('venv_path', self._default_venv_path),
                    vm_host=True,
                    gn_server_crt=p_config.get('gn_server_crt', open(str(p / 'gnscrt.bin'), 'rb').read()),
                    vmhostConfig=s_config,
                    host=p_config.get('host', '0.0.0.0'),
                    log_path=p_config.get('log_path', None),
                    no_checkServerHealth=p_config.get('NoCheckServerHealth', False)

                )

        if run:
            p = Path(servers_config_dir) / 'vmhost'
            s_config = {}
            if os.path.exists(str(p / 'config.json')):
                s_config = json.load(open(str(p / 'config.json')))

            p_config = {}
            if os.path.exists(str(p / 'hostconfig.json')):
                p_config = json.load(open(str(p / 'hostconfig.json')))


            bc = Path(p / 'baseconfig.json')

            if bc.exists():
                bconfig = json.load(open(str(bc)))
                for i in [
                    "VenvPath",
                    "LogDir"
                ]:
                    if i not in s_config and i in bconfig: # type: ignore
                        s_config[i] = bconfig[i] # type: ignore

            if 'CloudHostDomain' in s_config: # type: ignore
                self.setCloudHostDomain(cast(str, s_config['CloudHostDomain'])) # type: ignore
            if 'TelegramBotAlerts' in s_config: # type: ignore
                token = cast(str, s_config['TelegramBotAlerts']['token']) # type: ignore
                chat_ids = cast(List[int], s_config['TelegramBotAlerts']['chat_ids']) # type: ignore
                self.setTelegramBotAlerts(token, chat_ids)
            if 'VenvPath' in s_config: # type: ignore
                self.setVenvPath(cast(str, s_config['VenvPath'])) # type: ignore
            if 'LogDir' in s_config: # type: ignore
                self.setLogDir(cast(str, s_config['LogDir'])) # type: ignore
                                        
            
            self.run(
                domain=_domain_from_web2_to_web5(cast(str, s_config['domain'])),
                port=cast(dict, s_config).get('port', 40001),
                gn_server_crt=cast(dict, s_config).get('gn_server_crt', open(str(p / 'gnscrt.bin'), 'rb').read()),
                host=cast(dict, s_config).get('host', '0.0.0.0')
            )


    def setTelegramBotAlerts(self, token: str, chat_ids: List[int]):
        import httpx
        self.tgbot = (token, chat_ids, httpx.AsyncClient())

    def dispatchAlert(self, msg: str):
        if self.tgbot is None:
            return

        token, chat_ids, client = self.tgbot

        async def _(chat_id):
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'Markdown'
            }
            await client.post(url, json=payload)
        
        for i in chat_ids:
            asyncio.create_task(_(i))





    def setVenvPath(self, venv_path: str):
        self._default_venv_path = venv_path

    def setTLSPaths(self, cert_path: str, key_path: str) -> None:
        self._default_TLS_paths = (cert_path, key_path)

    def setLogDir(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)
        if os.path.exists(dir_path):
            self._log_dir_path = dir_path
        else:
            raise Exception('Путь не найден')

    def writeLog(self, domain: str, msg: str, prefix: str = ''):
        print(f"[{domain}]{prefix}: {msg}")
        file: Optional[AsyncLogWriter] = self._servers[domain].get('_log_file')
        if file is not None:
            file.write(msg)


    def addServerStartFile(self,
                           domain: str,
                           file_path: str,
                           port: Optional[int] = None,
                           start_when_run: bool = False,
                           venv_path: Optional[str] = None,
                           vm_host: bool = False,
                           gn_server_crt: Optional[Union[str, bytes]] = None,
                           vmhostConfig: Optional[Union[str, dict]] = None,
                           git_repo_auto_update: Union[bool, str] = False,

                           cert_path: Optional[str] = None,
                           key_path: Optional[str] = None,
                           host: str = '0.0.0.0',
                           log_path: Optional[str] = None,
                           no_checkServerHealth: bool = False
                           ):
        
        if log_path is None and self._log_dir_path is not None:
            log_path = self._log_dir_path + f'/{domain}/' + f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.log'

        if log_path:
            if not os.path.exists(log_path):
                os.makedirs(os.path.dirname(log_path), exist_ok=True)

            trim_old_files(os.path.dirname(log_path), self._log_max_files)

        gn_server_crt = _GNServer._normalize_gn_server_crt(gn_server_crt) if gn_server_crt is not None else None

        self._servers[domain] = {
            "domain": domain,
            "path": file_path,
            "port": port,
            "start_when_run": start_when_run,
            "venv_path": venv_path if venv_path is not None else self._default_venv_path,
            "vm_host": vm_host,
            "git_repo_auto_update": git_repo_auto_update,

            "cert_path": cert_path if cert_path is not None else self._default_TLS_paths[0] if self._default_TLS_paths is not None else None,
            "key_path": key_path if key_path is not None else self._default_TLS_paths[1] if self._default_TLS_paths is not None else None,
            "host": host,
            "log_path": log_path,
            "gn_server_crt_data_raw_bytes": gn_server_crt,
            "vmhostConfig": vmhostConfig,
            "no_checkServerHealth": no_checkServerHealth
            }

        
        if log_path is not None:
            file = AsyncLogWriter(log_path)
            
            self._servers[domain]["_log_file"] = file

    async def startLikeRun(self):
        for server in self._servers:
            if self._servers[server]["start_when_run"]:
                asyncio.create_task(self.startServer(server))


    async def startServer(self, domain: str, timeout: float = 30):
        if self._startType == 'gn-server-vm-host-environment':
            self.runGNServerVMHostEnvironment(run=False) # just update servers list

        if domain not in self._servers:
            self.writeLog(domain, f'No server start file found with domain: {domain}')
            raise ValueError(f"No server start file found with domain: {domain}")

        # Проверка что уже запущен
        res = await self.checkServerHealth(domain, timeout=1.0, dis_no_checkServerHealth=True)
        if res[0]:
            return (f"Server already running: {domain}")

        server = self._servers[domain]
        path = server["path"]
        port = server["port"]
        venv_path = server["venv_path"]
        vm_host = server['vm_host']
        host = server['host']

        cert_path = server['cert_path']
        key_path = server['key_path']

        if vm_host and (cert_path is None or key_path is None) and server['gn_server_crt_data_raw_bytes'] is None:
            raise Exception('Не указаны сертификаты')

        if not os.path.isfile(path):
            raise ValueError(f"Server start file not found: {path}")


        out_ = None

        if vm_host:
            if port is not None and is_port_in_use(port, 'udp'):
                _kill_process_by_port(port)
                await asyncio.sleep(1)

            if server['git_repo_auto_update'] is not False:
                if server['git_repo_auto_update'] is True:
                    __path = f'{home}/GW/GN/servers/{_domain_from_web5_to_web2(domain)}'
                    if not os.path.exists(__path):
                        __path = f'{home}/GW/GN/servers/gns-{_domain_from_web5_to_web2(domain)}'
                else:
                    __path = server['git_repo_auto_update']

                subprocess.run(
                    [f"{home}/GW/GN/vmhost/update_git_repo.sh", __path],
                    check=True
                )
            

            if venv_path is not None:
                if not os.path.isdir(venv_path):
                    raise ValueError(f"Virtual environment path not found: {venv_path}")
                python_executable = os.path.join(venv_path, 'bin', 'python')
                if not os.path.isfile(python_executable):
                    raise ValueError(f"Python executable not found in virtual environment: {python_executable}")
            else:
                python_executable = sys.executable

            if not vm_host:
                argv = {}
            else:
                argv = {
                    'command': 'gn:vm-host:start',
                    'domain': str(domain),
                    'port': str(port),
                    'host': str(host)
                }
            
            if cert_path is not None:
                argv['cert_path'] = cert_path

            if key_path is not None:
                argv['key_path'] = key_path

            
            if server['gn_server_crt_data_raw_bytes'] is not None:
                argv['gn_server_crt'] = server['gn_server_crt_data_raw_bytes']
            
            if server['vmhostConfig'] is not None:
                argv['vmhostConfig'] = server['vmhostConfig']

            raw_argv = userFriendly.encode(serialize(argv))

            self.writeLog(domain, 'Server starting...')

            # асинхронный запуск процесса
            proc = await asyncio.create_subprocess_exec(
                python_executable, path, raw_argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            save_out = []

            async def log_stream(stream: asyncio.StreamReader, prefix: str):
                async for line in stream:
                    text = line.decode().rstrip()
                    save_out.append(text)
                    self.writeLog(domain, text, prefix)

            # запускаем таски на чтение stdout/stderr
            asyncio.create_task(log_stream(proc.stdout, "OUT")) # type: ignore
            asyncio.create_task(log_stream(proc.stderr, "ERR")) # type: ignore

            try:
                # ждём чуть-чуть: если процесс сразу сдохнет — фиксируем
                returncode = await asyncio.wait_for(proc.wait(), timeout=3)
                self.writeLog(domain, f"Process exited with code {returncode}")
                save_out.clear()
            except asyncio.TimeoutError:
                self.writeLog(domain, "Process timed out")
                out_ = '\n'.join(save_out)

        else:
            self.writeLog(domain, 'Server starting...')
            proc = await asyncio.create_subprocess_exec(
                path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            save_out = []
            async def log_stream(stream: asyncio.StreamReader, prefix: str):
                async for line in stream:
                    text = line.decode().rstrip()
                    save_out.append(text)
                    self.writeLog(domain, text, prefix)

            # запускаем таски на чтение stdout/stderr
            asyncio.create_task(log_stream(proc.stdout, "OUT")) # type: ignore
            asyncio.create_task(log_stream(proc.stderr, "ERR")) # type: ignore

        server['proc'] = proc

        await asyncio.sleep(5)
        r = await self.checkServerHealth(domain, timeout=timeout, out=out_)
        s = r[0]
        self.writeLog(domain, f'Server checkServerHealth status-> {s}')
        if s:
            self.dispatchAlert(f'Сервер {domain} успешно запущен')
        else:
            if not path.endswith('.py'):
                self.dispatchAlert(f'Сервер {domain} запущен')
            else:
                self.dispatchAlert(f'Сервер {domain} запущен с ошибкой')
        return r


    async def _send_message_to_server(self, domain: str, path: str, payload: Optional[dict] = None, timeout: float = 1.0, res: list = []) -> Optional[GNResponse]:
        port = self._servers[domain].get("port")
        if port is None:
            return responses.ok()

        if path.startswith('/'):
            path = path[1:]

        c = self._app.client.request(GNRequest('post', Url(f'gn://[::1]:{port}/!gn-vm-host/{path}'), payload=payload), reconnect_wait=2)
        

        print(f'send request timeout: {timeout} (port: {port})')

        try:
            result = await asyncio.wait_for(c, timeout=timeout)
        except asyncio.TimeoutError:
            result = None
        
        res.append(result)

    async def checkServerHealth(self, domain: str, timeout: float = 3.0, interval=5, out: Optional[str] = None, dis_no_checkServerHealth: bool = False) -> Tuple[bool, Optional[str], Optional[GNResponse]]:
        loop = asyncio.get_event_loop()
        end = loop.time() + timeout
        res = []
        count = 0

        s = self._servers.get(domain)
        if s is None:
            raise ValueError(f"No server start file found with domain: {domain}")
        
        if not dis_no_checkServerHealth and 'no_checkServerHealth' in s and s['no_checkServerHealth']:
            return (True, out, None)

        while loop.time() < end:
            if 'starting_complete' in s and s['starting_complete'][0]:
                if s['starting_complete'][1] + datetime.timedelta(seconds=10) < datetime.datetime.now():
                    return (True, out, None)

            loop.create_task(self._send_message_to_server(domain, '/ping', timeout=timeout - interval * count, res=res))
            count+=1

            await asyncio.sleep(0.05)

            if res != []:
                return (True, out, res[0])
            else:
                await asyncio.sleep(interval)
            
        return (False, out, None)

    def stopServer(self, domain: str):
        if domain in self._servers:
            server = self._servers[domain]
            
            proc: asyncio.subprocess.Process = server.get('proc')
            if proc is not None:
                try:
                    proc.kill()
                except: pass
            else:
                port = server["port"]
                if port is not None:
                    _kill_process_by_port(port)
                else:
                    raise ValueError(f"No port specified for server: {domain}")
        else:
            raise ValueError(f"No server start file found with domain: {domain}")
        self.dispatchAlert(f'Сервер {domain} успешно остановлен')

    async def reloadServer(self, domain: str, timeout: float = 1):
        if domain in self._servers:
            self.stopServer(domain)
            await asyncio.sleep(timeout)
            return await self.startServer(domain)
        else:
            raise ValueError(f"No server start file found with domain: {domain}")

    def run(self,
            domain: str,
            port: int,
            gn_server_crt: Union[str, bytes, Path],
            *,
            host: str = '0.0.0.0',
            idle_timeout: float = 20.0,
            wait: bool = True
            ):

        self._app.run(
            domain=domain,
            port=port,
            gn_server_crt=gn_server_crt,
            host=host,
            idle_timeout=idle_timeout,
            wait=wait,
            run=self.startLikeRun,
        )


    def __resolve_access_key(self, request: GNRequest) -> None:
        if self._cloud_host_domain is None:
            raise responses.app.Forbidden("Cloud domain is not set")
        
        if request.client.domain != self._cloud_host_domain:
            self.writeLog(self._cloud_host_domain, f'Access denied for domain: {request.client.domain}')
            raise responses.app.Forbidden("Access denied")

    def __add_routes(self):

        @self._app.route('post', '/s/starting-complete')
        async def _route_post_s_starting_complete(request: GNRequest):
            
            s = self._servers.get(request.client.domain)
            if s is None:
                self.writeLog(request.client.domain or '', f'No server start file found with domain: {request.client.domain}')
                raise responses.app.NotFound("Server not found")

            s['starting_complete'] = (True, datetime.datetime.now())
        
        @self._app.route('*', '/api/{path:path}')
        async def api_proxy_handler(request: GNRequest, path: str):
            self.__resolve_access_key(request)
            return request


        @self._app.route('post', '/api/ping')
        async def ping_handler(request: GNRequest, domain: Optional[str] = None, timeout: float = 3.0):
            if not domain:
                return responses.ok({'time': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            try:
                result = await self.checkServerHealth(domain, timeout=timeout)
                if result[0]:
                    try:
                        _time = result[2].payload.get('time')
                    except:
                        _time = None
                    return responses.ok({'message': f'Server {domain} is alive.', 'time': _time})
                else:
                    return GNResponse('error', {'error': f'Server {domain} is not responding.'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
                
        @self._app.route('get', '/api/servers')
        async def list_servers_handler(request: GNRequest):
            servers_info = []
            for server in self._servers.values():
                servers_info.append(server['domain'])
            return responses.ok({'servers': servers_info})

        @self._app.route('post', '/api/start-server')
        async def start_server_handler(request: GNRequest, domain: str = ''):
            try:
                result = await self.startServer(domain)
                if result[0]:
                    return responses.ok({'message': f'Server {domain} started.'})
                else:
                    return GNResponse('error', {'error': f'Server {domain} failed to start within the timeout period. {result[1]}'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})

        @self._app.route('post', '/api/reload-server')
        async def reload_server_handler(request: GNRequest, domain: str = '', timeout: float = 0.5):
            try:
                result = await self.reloadServer(domain, timeout)
                if result[0]:
                    return responses.ok({'message': f'Server {domain} reloaded.'})
                else:
                    return GNResponse('error', {'error': f'Server {domain} failed to reload within the timeout period. {result[1]}'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
        
        @self._app.route('post', '/api/stop-server')
        async def stop_server_handler(request: GNRequest, domain: str = ''):
            try:
                self.stopServer(domain)
                return responses.ok({'message': f'Server {domain} stopped.'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
        
        @self._app.route('post', '/api/start-all-servers')
        async def start_all_servers_handler(request: GNRequest):
            for server in self._servers:
                try:
                    result = await self.startServer(server)
                    if not result:
                        return GNResponse('error', {'error': f'Server {server} failed to start within the timeout period.'})
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})
        
        @self._app.route('post', '/api/stop-all-servers')
        async def stop_all_servers_handler(request: GNRequest):
            for server in self._servers:
                try:
                    self.stopServer(server)
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})

            return responses.ok({'message': 'All servers stopped.'})
        
        @self._app.route('post', '/api/reload-all-servers')
        async def reload_all_servers_handler(request: GNRequest, timeout: float = 0.5):
            for server in self._servers:
                try:
                    result = await self.reloadServer(server, timeout)
                    if not result:
                        return GNResponse('error', {'error': f'Server {server} failed to reload within the timeout period.'})
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})
