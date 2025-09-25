#### 一、获取 U2 API Token 和 Cookie。

U2 API Token 获取：

- 使用 https://github.com/kysdm/u2_api 

- 或者安装油猴脚本 https://greasyfork.org/zh-CN/scripts/428545 后，访问U2内部论坛任意一个帖子，会提示"U2种子历史记录 自动鉴权工具"，按照说明操作即可。

Cookie 获取自行解决。

#### 二、本地构建 autobrr_loadbalance 镜像

拉取仓库：https://github.com/xwell/autobrr_loadbalance，再构建，步骤如下：

```bash
git clone https://github.com/xwell/autobrr_loadbalance.git
cd autobrr_loadbalance && docker build -t qbittorrent-loadbalancer .
```

#### 三、拉取 u2_tools 并启动

拉取 https://github.com/xwell/u2_tools 仓库(git clone https://github.com/xwell/u2_tools.git && cd u2_tools )，然后按照如下步骤完成安装和设置。

1. 先配置 autobrr-lb，直接执行脚本 bash setup-autobrr-lb.sh 然后，根据提示，修改配置文件 qbt-loadbalancer-config/config.json`，在这里面配置你的多个qbittorrent客户端。（可选配置，可以自行修改 autobrr-lb加密信息："webhook_path": "/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789",`，然后对应 u2_tools 里也要修改）
2. 复制 u2_tools 的配置文件为 .env（操作 cp env.example .env`），并按照需要修改（必须要改的是：`U2_API_TOKEN 、 `U2_COOKIES`、`U2_UID`、`U2_AUTOBRR_LB_UP_LIMIT`）。注意：限速建议`49MB/s`；另外，如果你自行修改了上一步的 autobrr-lb 加密信息，那么对应也要修改 `U2_AUTOBRR_LB_PATH`。
3. 启动 u2_tools `bash start.sh`；
4. 启动 autobrr-lb：`bash manage-qbt-lb.sh start`