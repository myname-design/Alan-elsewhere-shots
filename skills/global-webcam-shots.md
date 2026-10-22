# Skill: 全球实况摄像头出图

用户点一个地名，拉当地实时摄像头画面，上传图床，在对话里贴出。

---

## 一、数据源

**SkylineWebcams**（免费、无需 key、全球覆盖）

- 国家/地区页：
  `https://www.skylinewebcams.com/en/webcam/{国家slug}.html`
  例：`united-states/new-york.html`

- 单机位页面：
  `https://www.skylinewebcams.com/en/webcam/united-states/new-york/new-york/{slug}.html`
  例：`times-square.html`、`empire-state-building.html`

- **图片直链（关键）**：
  `https://cdn.skylinewebcams.com/live{id}.jpg`
  ❌ 不是 `www.skylinewebcams.com/img/live{id}.jpg` —— 那个返回统一兜底图

---

## 二、完整流程

### 步骤 0：先算时区，判断当地是不是白天
用户在中国 UTC+8。出图前必须确认目标城市当地时间是白天，否则一片黑。
```bash
TZ=America/New_York date
TZ=Europe/Rome date
TZ=Pacific/Auckland date
```

### 步骤 1：拉地区页面
```bash
curl -sL -A 'Mozilla/5.0' 'https://www.skylinewebcams.com/en/webcam/united-states/new-york.html' \
  -o /tmp/cam.html -w '%{http_code}\n'
```
返回 200 才算拿到。

### 步骤 2：扒机位 id 与名称
卡片以 `alt="..."` 起始，其后 2500 字符内第一个 `live{id}` 就是该机位的 id。
脚本见本目录 `pair_cams.py`：
```bash
python3 pair_cams.py /tmp/cam.html
```
输出形如：
```
6127 New York - Times Square
846 New York - Empire State Building
```

### 步骤 3：拉图
```bash
cd /tmp
for e in "6127:times-square" "846:empire-state"; do
  id="${e%%:*}"; nm="${e##*:}"
  curl -sL -A 'Mozilla/5.0' "https://cdn.skylinewebcams.com/live${id}.jpg" -o "cam_${nm}.jpg"
  echo "$nm $(stat -c%s cam_${nm}.jpg)"
done
md5sum cam_*.jpg
```

### 步骤 4：验真（必做，跳过会发兜底图）
- 多张图 `stat -c%s` 尺寸**完全相同** + `md5sum` **全同** → 兜底图，链接或 id 错了，回步骤 2 重查
- md5 **各不相同** → 真图，继续

### 步骤 5：上传 GitHub 图床
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
**每个 sha 都要打印，FAIL 不能吞。** 全部成功才进下一步。

### 步骤 6：贴图
```
https://raw.githubusercontent.com/myname-design/Alan-elsewhere-shots/main/snaps/{STAMP}-{nm}.jpg
```
**有几张贴几张，一张不落。** 上传成功但漏贴是常见失误。

---

## 三、环境事实（踩过的坑）

| 项 | 结论 |
|---|---|
| 图床 token | `/root/elsewhere-mcp/.env` 里的 `GH_TOKEN` / `GH_REPO` |
| 仓库 | `myname-design/Alan-elsewhere-shots`，图片放 `snaps/` |
| 图片直链域名 | `cdn.skylinewebcams.com`，不是 `www` |
| 兜底图判据 | 多张尺寸相同 + md5 全同 |
| PIL | **未安装**，裁图用 ImageMagick `convert` |
| `file` 命令 | **不存在**，查类型用 `md5sum` / `stat` |
| `convert` | 可用，裁图放大：`convert in.jpg -crop WxH+X+Y +repage -resize 1800x1350! out.jpg` |
| jsdelivr | 连不上（CODE=000），别指望从那取 js |
| 视频流 | SkylineWebcams 的 m3u8 是 JS 动态拼 + 防盗链，后台扒不出来。**要动态只能给用户原页面链接，或连拍多帧拼 gif** |

---

## 四、工具调用纪律

- `super_admin:terminal` 的 `params` 必须是合法 JSON 对象
- 命令**尽量短**，多层引号用 heredoc 或写文件，别硬塞
- **单次输出别太长**，XML 标签被截断会导致「本轮所有工具调用作废」
- 命令被截断时，拆成多条小命令重发
- 不要用 `set -e` / `set -o errexit`，会让终端会话卡死

---

## 五、已知机位表

### 美国 · 纽约
| id | 名称 |
|---|---|
| 6127 | 时代广场 Times Square |
| 790 | 时代广场（另一机位）|
| 846 | 帝国大厦 Empire State Building |
| 544 | 百老汇广告牌 Broadway Billboards |
| 6064 | 跨年球 Ball Drop |
| 2598 | 时代广场播客视角 |
| 545 / 2692 | 布莱恩特公园 / 曼哈顿 |
| 4361 | 纽约港 City Harbor |
| 4426 | 纽约天际线 Skyline |
| 2183 | 1540 百老汇 |
| 3800 | 布鲁克林大桥 |
| 4910 | 东河 East River |
| 4152 / 4132 | 乔治华盛顿大桥 |
| 5914 | 世贸中心 World Trade Center |
| 4473 / 2184 | 中城曼哈顿 |
| 4131 | 康尼岛 Coney Island |
| 5921 | 罗杰斯海滩 |
| 3521 | 东汉普顿海滩 |
| 4988 | 老尼亚加拉堡 |
| 2843 | 水牛城 |

*其余地区机位：拉对应国家页 → 跑 pair_cams.py 现查。*

---

## 六、常见国家/地区 slug
`united-states` / `italy` / `switzerland` / `iceland` / `new-zealand` / `norway` / `japan` / `france` / `spain` / `greece` / `canada` / `australia`

细分页规则（以美国为例）：
`united-states/new-york.html` → 州级
`united-states/new-york/new-york/times-square.html` → 机位级
