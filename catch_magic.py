"""必填参数只有 cookie，之后修改 BK_DIR 和 WT_DIR，即可运行
依赖 pip3 install requests lxml bs4 loguru pytz
u2_api: https://github.com/kysdm/u2_api，自动获取 token: https://greasyfork.org/zh-CN/scripts/428545
"""

import gc
import json
import os
import re
import shutil
import pytz
import psutil
import signal
import sys
from pathlib import Path

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from time import sleep, time
from typing import Dict, List, Union, Any

from requests import get, ReadTimeout, ConnectTimeout
from bs4 import BeautifulSoup
from loguru import logger

# 环境变量配置支持
def get_env_config(key: str, default: Any = None, type_func: type = str) -> Any:
    """从环境变量获取配置，支持类型转换"""
    value = os.getenv(key, default)
    if value is None:
        return default
    try:
        if type_func == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif type_func == list:
            # 尝试解析为 JSON 数组
            if value.startswith('[') and value.endswith(']'):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            # 否则按逗号分割
            return [item.strip() for item in value.split(',') if item.strip()]
        elif type_func == dict:
            if value.startswith('{') and value.endswith('}'):
                return json.loads(value)
            # 支持 Cookie 字符串格式: "PHPSESSID=aaa; nexusphp_u2=bbb"
            elif '=' in value and (';' in value or 'nexusphp_u2' in value):
                cookies = {}
                for cookie in value.split(';'):
                    cookie = cookie.strip()
                    if '=' in cookie:
                        key, val = cookie.split('=', 1)
                        cookies[key.strip()] = val.strip()
                return cookies
            return {}
        else:
            return type_func(value)
    except (ValueError, TypeError):
        logger.warning(f"环境变量 {key} 的值 '{value}' 无法转换为 {type_func.__name__}，使用默认值 {default}")
        return default

# 基础配置
COOKIES = get_env_config('U2_COOKIES', {'nexusphp_u2': ''}, dict)
BK_DIR = get_env_config('U2_BK_DIR', '/app/data/backup', str)
WT_DIR = get_env_config('U2_WT_DIR', '/app/data/watch', str)
INTERVAL = get_env_config('U2_INTERVAL', 120, int)
API_TOKEN = get_env_config('U2_API_TOKEN', '', str)
UID = get_env_config('U2_UID', 50096, int)
RUN_CRONTAB = get_env_config('U2_RUN_CRONTAB', False, bool)
RUN_TIMES = get_env_config('U2_RUN_TIMES', 1, int)
PROXIES = get_env_config('U2_PROXIES', {'http': '', 'https': ''}, dict)
MAX_SEEDER_NUM = get_env_config('U2_MAX_SEEDER_NUM', 5, int)
LOG_PATH = get_env_config('U2_LOG_PATH', '/app/logs/catch_magic.log', str)
DATA_PATH = get_env_config('U2_DATA_PATH', '/app/data/catch_magic.data.txt', str)

# 内存监控配置
MEMORY_LIMIT_MB = get_env_config('U2_MEMORY_LIMIT_MB', 512, int)
MEMORY_CHECK_INTERVAL = get_env_config('U2_MEMORY_CHECK_INTERVAL', 300, int)  # 5分钟检查一次
FORCE_GC_THRESHOLD = get_env_config('U2_FORCE_GC_THRESHOLD', 0.8, float)  # 内存使用率超过80%时强制GC
# 下载策略配置
DOWNLOAD_NON_FREE = get_env_config('U2_DOWNLOAD_NON_FREE', False, bool)
MIN_DAY = get_env_config('U2_MIN_DAY', 7, int)
DOWNLOAD_OLD = get_env_config('U2_DOWNLOAD_OLD', True, bool)
DOWNLOAD_NEW = get_env_config('U2_DOWNLOAD_NEW', False, bool)
MAGIC_SELF = get_env_config('U2_MAGIC_SELF', False, bool)
EFFECTIVE_DELAY = get_env_config('U2_EFFECTIVE_DELAY', 60, int)
DOWNLOAD_DEAD_TO = get_env_config('U2_DOWNLOAD_DEAD_TO', False, bool)
RE_DOWNLOAD = get_env_config('U2_RE_DOWNLOAD', True, bool)
CHECK_PEERLIST = get_env_config('U2_CHECK_PEERLIST', False, bool)
DA_QIAO = get_env_config('U2_DA_QIAO', True, bool)
MIN_RE_DL_DAYS = get_env_config('U2_MIN_RE_DL_DAYS', 0, int)

# 过滤配置
CAT_FILTER = get_env_config('U2_CAT_FILTER', [], list)
SIZE_FILTER = get_env_config('U2_SIZE_FILTER', [0, -1], list)
NAME_FILTER = get_env_config('U2_NAME_FILTER', [], list)
# 网络请求配置
MIN_ADD_INTERVAL = get_env_config('U2_MIN_ADD_INTERVAL', 0, int)
REQUEST_TIMEOUT = get_env_config('U2_REQUEST_TIMEOUT', 20, int)

R_ARGS = {'cookies': COOKIES,
          'headers': {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36'},
          'timeout': REQUEST_TIMEOUT,
          'proxies': PROXIES
          }

# autobrr_lb 集成配置
USE_AUTOBRR_LB = get_env_config('U2_USE_AUTOBRR_LB', True, bool)
AUTOBRR_LB_URL = get_env_config('U2_AUTOBRR_LB_URL', 'http://localhost:5000', str)
AUTOBRR_LB_PATH = get_env_config('U2_AUTOBRR_LB_PATH', '/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789', str)
AUTOBRR_LB_CATEGORY = get_env_config('U2_AUTOBRR_LB_CATEGORY', 'U2-Magic', str)
AUTOBRR_LB_TIMEOUT = get_env_config('U2_AUTOBRR_LB_TIMEOUT', 10, int)
FALLBACK_TO_LOCAL = get_env_config('U2_FALLBACK_TO_LOCAL', True, bool)

# 健康检查配置
HEALTH_CHECK_PORT = get_env_config('U2_HEALTH_CHECK_PORT', 8080, int)
HEALTH_CHECK_PATH = get_env_config('U2_HEALTH_CHECK_PATH', '/health', str)


class CatchMagic:
    pre_suf = [['时区', '，点击修改。'], ['時區', '，點擊修改。'], ['Current timezone is ', ', click to change.']]

    def __init__(self):
        self.checked, self.magic_id_0, self.tid_add_time = deque([], maxlen=200), None, {}
        self.last_memory_check = time()
        self.last_gc_time = time()
        self.running = True
        self.health_status = {
            'status': 'healthy',
            'last_check': time(),
            'memory_usage_mb': 0,
            'total_checks': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'uptime': time()
        }
        
        # 确保目录存在
        self._ensure_directories()
        
        # 加载数据
        self._load_data()
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 验证配置
        self._validate_configuration()
        
        # 显示当前配置模式
        self._log_configuration()
        
        logger.info(f"CatchMagic 初始化完成，内存限制: {MEMORY_LIMIT_MB}MB")

    def _ensure_directories(self):
        """确保必要的目录存在"""
        for directory in [BK_DIR, WT_DIR, os.path.dirname(LOG_PATH), os.path.dirname(DATA_PATH)]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        """加载持久化数据"""
        try:
            with open(DATA_PATH, 'a', encoding='utf-8'):
                pass
            with open(DATA_PATH, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                self.checked = deque(data['checked'], maxlen=200)
                self.magic_id_0 = data['id_0']
                self.tid_add_time = data['add_time']
        except (json.JSONDecodeError, FileNotFoundError):
            logger.info("未找到数据文件，将创建新的数据文件")
        self.first_time = True

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在优雅关闭...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _validate_configuration(self):
        """验证配置是否正确"""
        # 检查认证方式
        has_api_token = bool(API_TOKEN)
        has_cookie = bool(COOKIES.get('nexusphp_u2'))
        
        # Cookie 是必需的，因为获取种子下载链接需要 Cookie
        if not has_cookie:
            logger.error("配置错误: 必须设置 U2_COOKIES，因为获取种子下载链接需要 Cookie 认证")
            logger.error("Cookie 格式: PHPSESSID=aaa; nexusphp_u2=bbb")
            logger.error("或者 JSON 格式: {\"nexusphp_u2\": \"your_cookie\"}")
            raise ValueError("缺少必要的 Cookie 配置")
        
        if has_api_token:
            logger.info("同时设置了 API_TOKEN 和 COOKIES，将使用 API 获取魔法信息，Cookie 用于种子下载")
        else:
            logger.info("使用 Cookie 模式获取魔法信息和种子下载")
        
        # 检查必要的目录权限
        try:
            Path(BK_DIR).mkdir(parents=True, exist_ok=True)
            Path(WT_DIR).mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"目录权限错误: {e}")
            raise

    def check_memory_usage(self):
        """检查内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.health_status['memory_usage_mb'] = memory_mb
            
            if memory_mb > MEMORY_LIMIT_MB:
                logger.warning(f"内存使用超过限制: {memory_mb:.1f}MB > {MEMORY_LIMIT_MB}MB")
                self.health_status['status'] = 'warning'
                return False
            elif memory_mb > MEMORY_LIMIT_MB * FORCE_GC_THRESHOLD:
                logger.info(f"内存使用率较高: {memory_mb:.1f}MB，执行垃圾回收")
                gc.collect()
                self.last_gc_time = time()
                
            self.health_status['status'] = 'healthy'
            return True
        except Exception as e:
            logger.error(f"检查内存使用情况时出错: {e}")
            return False

    def get_health_status(self):
        """获取健康状态"""
        self.health_status['last_check'] = time()
        self.health_status['uptime'] = time() - self.health_status['uptime']
        return self.health_status

    def _log_configuration(self):
        """显示当前配置模式"""
        # 显示数据获取方式
        if API_TOKEN:
            logger.info(f"=== API + Cookie 混合模式 ===")
            logger.info(f"API Token: {'已设置' if API_TOKEN else '未设置'}")
            logger.info(f"用户 ID: {UID}")
            logger.info(f"Cookie: {'已设置' if COOKIES.get('nexusphp_u2') else '未设置'}")
        else:
            logger.info(f"=== Cookie 模式 ===")
            logger.info(f"Cookie: {'已设置' if COOKIES.get('nexusphp_u2') else '未设置'}")
        
        # 显示下载方式
        if USE_AUTOBRR_LB:
            logger.info(f"=== autobrr_lb 模式已启用 ===")
            logger.info(f"负载均衡器地址: {AUTOBRR_LB_URL}")
            logger.info(f"Webhook 路径: {AUTOBRR_LB_PATH}")
            logger.info(f"种子分类: {AUTOBRR_LB_CATEGORY}")
            logger.info(f"回退机制: {'启用' if FALLBACK_TO_LOCAL else '禁用'}")
        else:
            logger.info(f"=== 本地下载模式 ===")
            logger.info(f"备份目录: {BK_DIR}")
            logger.info(f"监控目录: {WT_DIR}")
        logger.info("=" * 30)

    def info_from_u2(self):
        all_checked = True if self.first_time and not self.magic_id_0 else False
        index = 0
        id_0 = self.magic_id_0

        while True:
            soup = self.get_soup(f'https://u2.dmhy.org/promotion.php?action=list&page={index}')
            user_id = soup.find('table', {'id': 'info_block'}).a['href'][19:]

            for i, tr in filter(lambda tup: tup[0] > 0, enumerate(soup.find('table', {'width': '99%'}))):
                magic_id = int(tr.contents[0].string)
                if index == 0 and i == 1:
                    self.magic_id_0 = magic_id
                    if self.first_time and id_0 and magic_id - id_0 > 10 * INTERVAL:
                        all_checked = True
                if tr.contents[5].string in ['Expired', '已失效'] or magic_id == id_0:
                    all_checked = True
                    break

                if tr.contents[1].string in ['魔法', 'Magic', 'БР']:
                    if not tr.contents[3].a and tr.contents[3].string in ['所有人', 'Everyone', 'Для всех'] \
                            or MAGIC_SELF and tr.contents[3].a and tr.contents[3].a['href'][19:] == user_id:
                        if tr.contents[5].string not in ['Terminated', '终止', '終止', 'Прекращён']:
                            if tr.contents[2].a:
                                tid = int(tr.contents[2].a['href'][15:])
                                if magic_id not in self.checked:
                                    if self.first_time and all_checked:
                                        self.checked.append(magic_id)
                                    else:
                                        yield magic_id, tid
                                    continue

                if magic_id not in self.checked:
                    self.checked.append(magic_id)

            if all_checked:
                break
            else:
                index += 1  # 新增魔法数量不小于单页魔法数量

    def info_from_api(self):
        r_args = {'timeout': R_ARGS.get('timeout'), 'proxies': R_ARGS.get('proxies')}
        params = {'uid': UID, 'token': API_TOKEN, 'scope': 'public', 'maximum': 30}
        resp = get('https://u2.kysdm.com/api/v1/promotion', **r_args, params=params).json()
        pro_list = resp['data']['promotion']
        if MAGIC_SELF:
            params['scope'] = 'private'
            resp1 = get('https://u2.kysdm.com/api/v1/promotion', **r_args, params=params).json()
            pro_list.extend([pro_data for pro_data in resp1['data']['promotion'] if pro_data['for_user_id'] == UID])

        for pro_data in pro_list:
            magic_id = pro_data['promotion_id']
            tid = pro_data['torrent_id']
            if magic_id == self.magic_id_0:
                break
            if magic_id not in self.checked:
                if self.first_time and not self.magic_id_0:
                    self.checked.append(magic_id)
                else:
                    yield magic_id, tid
        self.magic_id_0 = pro_list[0]['promotion_id']

    def all_effective_magic(self):
        id_0 = self.magic_id_0

        if not API_TOKEN:
            yield from self.info_from_u2()
        else:
            try:
                yield from self.info_from_api()
            except Exception as e:
                logger.exception(e)
                yield from self.info_from_u2()

        if self.magic_id_0 != id_0:
            with open(f'{DATA_PATH}', 'w', encoding='utf-8') as fp:
                json.dump({'checked': list(self.checked), 'id_0': self.magic_id_0,
                           'add_time': self.tid_add_time}, fp)
        self.first_time = False

    def dl_to(self, to_info):
        tid = to_info['dl_link'].split('&passkey')[0].split('id=')[1]

        if tid in self.tid_add_time:
            if time() - self.tid_add_time[tid] < MIN_ADD_INTERVAL:
                logger.info(f'Torrent {tid} | You have downloaded this torrent < {MIN_ADD_INTERVAL} s')
                return

        if CHECK_PEERLIST and to_info['last_dl_time']:
            peer_list = self.get_soup(f'https://u2.dmhy.org/viewpeerlist.php?id={tid}')
            tables = peer_list.find_all('table')
            for table in tables or []:
                for tr in filter(lambda _tr: 'nowrap' in str(_tr), table):
                    if tr.get('bgcolor'):
                        logger.info(f"Torrent {tid} | you are already "
                                    f"{'downloading' if len(tr.contents) == 12 else 'seeding'} the torrent")
                        return

        # 检查是否已下载过
        if f'[U2].{tid}.torrent' in os.listdir(BK_DIR):
            if not RE_DOWNLOAD:
                logger.info(f'Torrent {tid} | you have downloaded this torrent before')
                return

        # 根据配置选择下载方式
        if USE_AUTOBRR_LB:
            success = self._push_to_autobrr_lb(to_info, tid)
            if not success and FALLBACK_TO_LOCAL:
                logger.warning(f"autobrr_lb 推送失败，回退到本地下载: {to_info['to_name']}")
                self._download_to_local(to_info, tid)
        else:
            self._download_to_local(to_info, tid)

    def _push_to_autobrr_lb(self, to_info, tid):
        """推送到 autobrr_lb 负载均衡器"""
        try:
            import requests
            
            payload = {
                'release_name': to_info['to_name'],
                'download_url': to_info['dl_link'],
                'indexer': 'U2-DMHY',
                'category': AUTOBRR_LB_CATEGORY
            }
            
            response = requests.post(
                f'{AUTOBRR_LB_URL}{AUTOBRR_LB_PATH}',
                json=payload,
                timeout=AUTOBRR_LB_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.info(f"成功推送种子到 autobrr_lb: {to_info['to_name']} (ID: {tid})")
                self.tid_add_time[tid] = time()
                self.health_status['successful_downloads'] += 1
                return True
            else:
                logger.error(f"推送种子到 autobrr_lb 失败: {to_info['to_name']}, 状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"推送种子到 autobrr_lb 时出错: {e}")
            return False

    def _download_to_local(self, to_info, tid):
        """下载种子到本地目录（原始方式）"""
        try:
            # 下载种子文件到备份目录
            if f'[U2].{tid}.torrent' not in os.listdir(BK_DIR):
                with open(f'{BK_DIR}/[U2].{tid}.torrent', 'wb') as f:
                    f.write(get(to_info['dl_link'], **R_ARGS).content)

            # 复制到监控目录
            shutil.copy(f'{BK_DIR}/[U2].{tid}.torrent', f'{WT_DIR}/[U2].{tid}.torrent')
            logger.info(f"下载种子到本地: {to_info['to_name']} (ID: {tid})")
            self.tid_add_time[tid] = time()
            self.health_status['successful_downloads'] += 1
            return True
            
        except Exception as e:
            logger.error(f"下载种子到本地时出错: {e}")
            return False

    @classmethod
    def get_tz(cls, soup):
        tz_info = soup.find('a', {'href': 'usercp.php?action=tracker#timezone'})['title']
        tz = [tz_info[len(pre):-len(suf)].strip() for pre, suf in cls.pre_suf if tz_info.startswith(pre)][0]
        return pytz.timezone(tz)

    @staticmethod
    def timedelta(date, timezone):
        dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        return time() - timezone.localize(dt).timestamp()

    @staticmethod
    def get_pro(td):
        pro = {'ur': 1.0, 'dr': 1.0}
        pro_dict = {'free': {'dr': 0.0}, '2up': {'ur': 2.0}, '50pct': {'dr': 0.5}, '30pct': {'dr': 0.3}, 'custom': {}}
        for img in td.select('img') or []:
            if not [pro.update(data) for key, data in pro_dict.items() if key in img['class'][0]]:
                pro[{'arrowup': 'ur', 'arrowdown': 'dr'}[img['class'][0]]] = float(img.next.text[:-1].replace(',', '.'))
        return list(pro.values())

    @staticmethod
    def get_soup(url):
        magic_page = get(url, **R_ARGS).text
        if url != 'https://u2.dmhy.org/promotion.php?action=list&page=0':
            logger.debug(f'Download page: {url}')
        return BeautifulSoup(magic_page.replace('\n', ''), 'lxml')

    def analyze_magic(self, magic_id, tid):
        soup = self.get_soup(f'https://u2.dmhy.org/details.php?id={tid}')
        aa = soup.select('a.index')
        if len(aa) < 2:
            logger.info(f'Torrent {tid} | torrent deleted, passed')
            return
        to_info = {'to_name': aa[0].text[5:-8], 'dl_link': f"https://u2.dmhy.org/{aa[1]['href']}"}

        if NAME_FILTER:
            title = soup.find('h1', {'align': 'center', 'id': 'top'}).text
            if any(st in title or st in to_info['to_name'] for st in NAME_FILTER):
                logger.debug(f'Torrent {tid} | torrent excluded by NAME_FILTER')
                return

        if CAT_FILTER:
            cat = soup.time.parent.contents[7].strip()
            if cat not in CAT_FILTER:
                logger.debug(f'Torrent {tid} | torrent category {cat} does not match, passed')
                return

        if SIZE_FILTER and not (SIZE_FILTER[0] <= 0 and SIZE_FILTER[1] == -1):
            size_str = soup.time.parent.contents[5].strip().replace(',', '.').replace('Б', 'B')
            [num, unit] = size_str.split(' ')
            _pow = ['MiB', 'GiB', 'TiB', '喵', '寄', '烫', 'egamay', 'igagay', 'eratay'].index(unit) % 3
            gb = float(num) * 1024 ** (_pow - 1)
            if gb < SIZE_FILTER[0] or SIZE_FILTER[1] != -1 and gb > SIZE_FILTER[1]:
                logger.debug(f'Torrent {tid} | torrent size {size_str} does not match, passed')
                return

        if CHECK_PEERLIST or MIN_RE_DL_DAYS > 0:
            for tr in soup.find('table', {'width': '90%'}):
                if tr.td.text in ['My private torrent', '私人种子文件', '私人種子文件', 'Ваш личный торрент']:
                    time_str = tr.find_all('time')
                    if not time_str:
                        to_info['last_dl_time'] = None
                    else:
                        date = time_str[1].get('title') or time_str[1].text
                        to_info['last_dl_time'] = time() - self.timedelta(date, self.get_tz(soup))
            if MIN_RE_DL_DAYS > 0 and to_info['last_dl_time']:
                if time() - to_info['last_dl_time'] < 86400 * MIN_RE_DL_DAYS:
                    logger.debug(f"Torrent {tid} | You have downloaded this torrent "
                                 f"{(time() - to_info['last_dl_time']) // 86400} days before, passed")
                    return

        delta = self.timedelta(soup.time.get('title') or soup.time.text, self.get_tz(soup))
        seeder_count = int(re.search(r'(\d+)', soup.find('div', {'id': 'peercount'}).b.text).group(1))
        magic_page_soup = None

        if delta < MIN_DAY * 86400:
            if DOWNLOAD_NEW:
                if seeder_count > MAX_SEEDER_NUM:
                    logger.debug(f'Torrent {tid} | seeders > {MAX_SEEDER_NUM}, passed')
                else:
                    if [self.get_pro(tr.contents[1])[1] for tr in soup.find('table', {'width': '90%'})
                        if tr.td.text in ['流量优惠', '流量優惠', 'Promotion', 'Тип раздачи (Бонусы)']][0] > 0:
                        logger.debug(f'torrent {tid} | is not free, passed')
                    else:
                        self.dl_to(to_info)
            else:
                logger.debug(f'Torrent {tid} | time < {MIN_DAY} days, passed')
            return
        elif not DOWNLOAD_OLD:
            logger.debug(f'Torrent {tid} | time > {MIN_DAY} days, passed')
            return

        if not DOWNLOAD_NON_FREE:
            if [self.get_pro(tr.contents[1])[1] for tr in soup.find('table', {'width': '90%'})
                    if tr.td.text in ['流量优惠', '流量優惠', 'Promotion', 'Тип раздачи (Бонусы)']][0] > 0:
                logger.debug(f'torrent {tid} | is not free, will pass if no free magic in delay.')
                magic_page_soup = self.get_soup(f'https://u2.dmhy.org/promotion.php?action=detail&id={magic_id}')
                tbody = magic_page_soup.find('table', {'width': '75%', 'cellpadding': 4}).tbody
                if self.get_pro(tbody.contents[6].contents[1])[1] == 0:
                    time_tag = tbody.contents[4].contents[1].time
                    delay = -self.timedelta(time_tag.get('title') or time_tag.text, self.get_tz(magic_page_soup))
                    if -1 < delay < EFFECTIVE_DELAY:
                        logger.debug(f'Torrent {tid} | free magic {magic_id} will be effective in {int(delay)}s')
                    else:
                        return
                else:
                    return

        if seeder_count > 0 or DOWNLOAD_DEAD_TO:
            if seeder_count <= MAX_SEEDER_NUM:
                self.dl_to(to_info)
                return
            elif DA_QIAO:
                if not magic_page_soup:
                    magic_page_soup = self.get_soup(f'https://u2.dmhy.org/promotion.php?action=detail&id={magic_id}')
                comment = magic_page_soup.legend.parent.contents[1].text
                if '搭' in comment and '桥' in comment or '加' in comment and '速' in comment:
                    user = magic_page_soup.select('table.main bdo')[0].text
                    logger.info(f'Torrent {tid} | user {user} is looking for help, downloading...')
                    self.dl_to(to_info)
                    return
            logger.debug(f'Torrent {tid} | seeders > {MAX_SEEDER_NUM}, passed')
        else:
            logger.debug(f'Torrent {tid} | no seeders, passed')

    def run(self):
        """运行一次检查循环"""
        if not self.running:
            return False
            
        # 定期检查内存使用情况
        if time() - self.last_memory_check > MEMORY_CHECK_INTERVAL:
            if not self.check_memory_usage():
                logger.warning("内存使用异常，跳过本次检查")
                return False
            self.last_memory_check = time()
        
        self.health_status['total_checks'] += 1
        id_0 = self.magic_id_0
        
        try:
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(self.analyze_magic, magic_id, tid): magic_id
                           for magic_id, tid in self.all_effective_magic()}
                if futures:
                    error = False
                    for future in as_completed(futures):
                        if not self.running:
                            break
                        try:
                            future.result()
                            self.checked.append(futures[future])
                        except Exception as er:
                            error = True
                            self.health_status['failed_downloads'] += 1
                            if isinstance(er, (ReadTimeout, ConnectTimeout)):
                                logger.error(f"网络超时: {er}")
                            else:
                                logger.exception(f"处理种子时出错: {er}")
                    
                    if error:
                        self.magic_id_0 = id_0
                        logger.warning("本次检查出现错误，回滚 magic_id_0")
                    
                    # 保存数据
                    self._save_data()
                    
        except Exception as e:
            logger.error(f"运行检查时出现严重错误: {e}")
            self.health_status['status'] = 'error'
            return False
        
        return True

    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(f'{DATA_PATH}', 'w', encoding='utf-8') as fp:
                json.dump({'checked': list(self.checked), 'id_0': self.magic_id_0,
                           'add_time': self.tid_add_time}, fp)
        except Exception as e:
            logger.error(f"保存数据时出错: {e}")


def start_health_server(catch):
    """启动健康检查服务器"""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == HEALTH_CHECK_PATH:
                    health_status = catch.get_health_status()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(health_status, indent=2).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # 禁用健康检查的访问日志
                pass
        
        server = HTTPServer(('0.0.0.0', HEALTH_CHECK_PORT), HealthHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"健康检查服务器已启动，端口: {HEALTH_CHECK_PORT}")
        return server
    except Exception as e:
        logger.warning(f"启动健康检查服务器失败: {e}")
        return None

@logger.catch()
def main(catch):
    """主运行循环"""
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    for _ in range(RUN_TIMES):
        if not catch.running:
            logger.info("收到停止信号，退出主循环")
            break
            
        try:
            success = catch.run()
            if success:
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"连续 {max_consecutive_errors} 次运行失败，退出程序")
                    break
                    
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"主循环出现异常: {e}")
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"连续 {max_consecutive_errors} 次运行失败，退出程序")
                break
        finally:
            if _ != RUN_TIMES - 1 or not RUN_CRONTAB:
                # 定期垃圾回收
                if time() - catch.last_gc_time > 3600:  # 1小时执行一次
                    gc.collect()
                    catch.last_gc_time = time()
                
                # 检查是否需要停止
                if catch.running:
                    sleep(INTERVAL)

def run_long_term():
    """长时间运行模式"""
    logger.info("启动长时间运行模式")
    catch = CatchMagic()
    
    # 启动健康检查服务器
    health_server = start_health_server(catch)
    
    try:
        while catch.running:
            main(catch)
            if catch.running:
                logger.info(f"等待 {INTERVAL} 秒后进行下一轮检查...")
                sleep(INTERVAL)
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    finally:
        catch.running = False
        if health_server:
            health_server.shutdown()
        logger.info("程序已退出")

# 配置日志
logger.remove()  # 移除默认处理器
logger.add(
    sink=LOG_PATH,
    level='DEBUG',
    rotation='10 MB',
    retention='7 days',
    compression='zip',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
    encoding='utf-8'
)
logger.add(
    sink=sys.stdout,
    level='INFO',
    format='<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}'
)

if __name__ == '__main__':
    if RUN_CRONTAB:
        # 定时任务模式
        logger.info("启动定时任务模式")
        c = CatchMagic()
        main(c)
    else:
        # 长时间运行模式
        run_long_term()
