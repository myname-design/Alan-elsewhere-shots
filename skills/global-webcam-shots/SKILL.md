---
name: global-webcam-shots
description: 全球实况摄像头出图。当用户说想看某地实时画面、实况、现在长什么样、天气怎么样、街上人多不多，或直接报地名要求看图时使用。自动找源、拉图、验真、上传图床、贴出可显示的图片链接。覆盖 SkylineWebcams / Windy / 官方旅游站 / 浏览器兜底四条路径。
---
# 全球实况摄像头出图

用户报一个地名 → 找到当地实时摄像头 → 拉图 → 验真 → 上传图床 → 贴出可访问的图片 URL。

**核心难点不是找图，是「本地图片发不出去」。** 对话里能显示的图必须是公网 URL，所以上传图床这一步不可省。

---

## 一、开工前：算时区

用户在中国（UTC+8）。目标城市当地不是白天就别拉了，一片黑没意义。

```bash
TZ=America/New_York date
TZ=Europe/Rome date
TZ=Asia/Seoul date
TZ=Pacific/Auckland date
```

常用：纽约 UTC-4、首尔/东京 UTC+9、意大利/瑞士 UTC+2、新西兰 UTC+12/13。

---

## 二、找源：四级路径，按序试，前面成了就不往下走

### 路径 1：SkylineWebcams（首选，最稳，免 key）

- 地区页：`https://www.skylinewebcams.com/en/webcam/{国家slug}.html`
  例：`united-states/new-york.html`、`italy.html`、`south-korea.html`
- 图片直链：`https://cdn.skylinewebcams.com/live{id}.jpg`
  ❌ **不是** `www.skylinewebcams.com/img/live{id}.jpg`，那个返回统一兜底图
- 扒 id：`python3 scripts/pair_cams.py /tmp/cam.html`
- **覆盖有限**：韩国只有首尔、釜山，没有济州岛。遇到没有的，走路径 2。

### 路径 2：Windy（覆盖最广）

- 网页：`https://www.windy.com/-Webcams/webcams`
- API：`https://api.windy.com/webcams/api/v3/webcams?country=KR&limit=20&include=images`
  需要 API key（免费申请），放 header `x-windy-api-key`。
- 返回 JSON 里有 `images.current.preview` 直链，curl 下来即可。
- **没有 key 时**：直接开网页版，用浏览器工具（路径 4）截屏。

### 路径 3：本地官方站

旅游局、景区官网常有实况页。但多数是 YouTube 嵌入 —— **YouTube 直播后台拿不到帧，这是死路，别在 curl 上耗**。

### 路径 4：浏览器兜底（前三条全废时）

页面纯前端渲染、或 Cloudflare 403，curl 一律拿不到。这时必须走真浏览器：

- 用 `browser` 包（Playwright）打开页面，等加载完
- 抓 `img` 的 `src`，或直接截屏
- **不要用 curl 硬刚 403**，浪费时间

---

## 三、拉图与验真

```bash
cd /tmp
for e in "6127:times-square" "846:empire-state"; do
  id="${e%%:*}"; nm="${e##*:}"
  curl -sL -A 'Mozilla/5.0' "https://cdn.skylinewebcams.com/live${id}.jpg" -o "cam_${nm}.jpg"
  echo "$nm $(stat -c%s cam_${nm}.jpg)"
done
md5sum cam_*.jpg
```

**验真铁律**：
- 多张 `stat -c%s` 尺寸**完全相同** + `md5sum` **全同** → 兜底图，链接或 id 错了，回上一步重查
- md5 **各不相同** → 真图

---

## 四、上传图床（关键，不能省）

对话里显示的图必须是公网 URL，本地文件贴不出来。

```bash
cd /tmp && source /root/elsewhere-mcp/.env 2>/dev/null; export GH_TOKEN GH_REPO
STAMP=$(date -u +%Y%m%d-%H%M%S)
for nm in times-square empire-state; do
  b64=$(base64 -w0 cam_${nm}.jpg)
  python3 -c "import json,sys; print(json.dumps({'message':'shot '+sys.argv[1],'content':sys.argv[2]}))" "$nm" "$b64" > /tmp/u_${nm}.json
  curl -s -X PUT "https://api.github.com/repos/${GH_REPO}/contents/snaps/${STAMP}-${nm}.jpg" \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    --data-binary @/tmp/u_${nm}.json > /tmp/u_${nm}_r.json
  python3 -c "import json;d=json.load(open('/tmp/u_${nm}_r.json'));print('$nm', d.get('content',{}).get('sha','FAIL:'+str(d.get('message'))))"
done
echo "STAMP=$STAMP"
```

- token 在 `/root/elsewhere-mcp/.env` 的 `GH_TOKEN` / `GH_REPO`
- 仓库 `myname-design/Alan-elsewhere-shots`，图放 `snaps/`
- **每个 sha 必须打印，FAIL 不能吞**

---

## 五、贴图

```
https://raw.githubusercontent.com/myname-design/Alan-elsewhere-shots/main/snaps/{STAMP}-{nm}.jpg
```

**有几张贴几张，一张不落。** 上传成功却漏贴是最常见的失误。

---

## 六、环境事实（踩过的坑，别重踩）

| 项 | 结论 |
|---|---|
| 图片直链域名 | `cdn.skylinewebcams.com`，不是 `www` |
| 兜底图判据 | 多张尺寸相同 + md5 全同 |
| PIL | **未安装**，裁图用 ImageMagick `convert` |
| `file` 命令 | **不存在**，查类型用 `md5sum` / `stat` |
| `convert` | 可用：`convert in.jpg -crop WxH+X+Y +repage -resize 1800x1350! out.jpg` |
| jsdelivr | 连不上（CODE=000） |
| YouTube 直播 | 后台拿不到帧，死路 |
| Cloudflare 403 | 换浏览器工具，别 curl 硬刚 |

---

## 七、工具调用纪律

- `super_admin:terminal` 的 `params` 必须是合法 JSON 对象
- 命令**尽量短**，多层引号用 heredoc 或写文件
- **单次输出别太长**，XML 标签截断会导致「本轮所有工具调用作废」
- 被截断就拆成多条小命令重发
- 不要用 `set -e` / `set -o errexit`，会让终端会话卡死

---

## 八、已知机位表

### 美国 · 纽约
| id | 名称 |
|---|---|
| 6127 / 790 | 时代广场 |
| 846 | 帝国大厦 |
| 544 | 百老汇广告牌 |
| 6064 | 跨年球 |
| 2598 | 时代广场播客视角 |
| 545 / 2692 | 布莱恩特公园 / 曼哈顿 |
| 4361 | 纽约港 |
| 4426 | 纽约天际线 |
| 2183 | 1540 百老汇 |
| 3800 | 布鲁克林大桥 |
| 4910 | 东河 |
| 4152 / 4132 | 乔治华盛顿大桥 |
| 5914 | 世贸中心 |
| 4473 / 2184 | 中城曼哈顿 |
| 4131 | 康尼岛 |
| 5921 | 罗杰斯海滩 |
| 3521 | 东汉普顿海滩 |
| 4988 | 老尼亚加拉堡 |
| 2843 | 水牛城 |

### 常见国家 slug
`united-states`、`italy`、`switzerland`、`iceland`、`new-zealand`、`norway`、`japan`、`south-korea`、`france`、`spain`、`greece`、`canada`、`australia`

细分页规则（美国例）：
`united-states/new-york.html` → 州级
`united-states/new-york/new-york/times-square.html` → 机位级

---

## 九、输出风格

- 先说要拉哪几个机位，再动手
- 贴图时每张配一句短说明（这个点人多人少、天亮了没）
- 别把流程念给用户听，用户要的是图
