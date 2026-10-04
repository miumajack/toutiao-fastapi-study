<#
=====================================================================
 重启服务.ps1  —— FastAPI 学习项目的服务重启助手
=====================================================================
 它按顺序做四件事:
   1. 清理掉所有还活着的 FastAPI 服务进程(包括没有登记的"幽灵"子进程)
   2. 复查端口是否真的空出来了
   3. 让你选要启动哪个练习项目
   4. 用 --reload 启动服务

 用法:
   .\重启服务.ps1                    交互式选项目, 默认 8000 端口
   .\重启服务.ps1 -Port 8001         换端口启动
   .\重启服务.ps1 -AppDir "day03-AI掘金头条-新闻模块\我的练习_test\toutiao_backend"
                                    跳过选择, 直接启动指定目录

 如果提示"禁止运行脚本", 在 PowerShell 里执行一次这个就好:
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
=====================================================================
#>

param(
    [string]$AppDir = "",
    [int]$Port = 8000
)

$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------
# 0. 找到仓库根目录, 以及虚拟环境里的 python
#    $PSScriptRoot 是"这个脚本自己所在的目录", 所以不管从哪里运行, 都能找对位置
# ---------------------------------------------------------------
$RepoRoot = $PSScriptRoot
if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "  [提示] 没找到 .venv\Scripts\python.exe, 改用系统 PATH 里的 python" -ForegroundColor Yellow
    $Python = "python"
}

# 查端口占用的小工具: 借 netstat 来问, 比 Get-NetTCPConnection 稳
function Get-PortListeners([int]$p) {
    netstat -ano | Select-String -Pattern ":${p}\s+.*LISTENING" | ForEach-Object {
        $parts = ($_.Line.Trim() -split '\s+')
        [pscustomobject]@{ Address = $parts[1]; Pid = $parts[-1] }
    }
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host " FastAPI 服务重启助手" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# ---------------------------------------------------------------
# 1. 清理旧的 FastAPI 进程
#    要抓三类: uvicorn 主进程 / 命令行里带 uvicorn 的 python / multiprocessing 派生出来的子进程
#    第三类是重点 —— 它就是那个占着端口却查不到身份的"幽灵"
# ---------------------------------------------------------------
Write-Host ""
Write-Host "[1/4] 清理还活着的 FastAPI 进程" -ForegroundColor Cyan

$allProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='uvicorn.exe'" -ErrorAction SilentlyContinue
$targets = @()

foreach ($p in $allProcs) {
    $cmd = ""
    if ($p.CommandLine) { $cmd = [string]$p.CommandLine }

    $isUvicorn  = ($p.Name -eq "uvicorn.exe") -or ($cmd -match "uvicorn")
    $isSpawnKid = $cmd -match "multiprocessing\.spawn"

    if ($isUvicorn -or $isSpawnKid) {
        $targets += [pscustomobject]@{ Id = $p.ProcessId; Name = $p.Name; Cmd = $cmd }
    }
}

if ($targets.Count -eq 0) {
    Write-Host "  没有找到需要清理的进程, 很干净" -ForegroundColor Green
}
else {
    foreach ($t in $targets) {
        Write-Host "  结束进程  PID $($t.Id)  ($($t.Name))" -ForegroundColor Yellow
        $short = $t.Cmd
        if ($short.Length -gt 100) { $short = $short.Substring(0, 100) + "..." }
        Write-Host "      $short" -ForegroundColor DarkGray
        Stop-Process -Id $t.Id -Force -ErrorAction SilentlyContinue
    }
}

# 给系统一点时间回收端口
Start-Sleep -Milliseconds 1000

# ---------------------------------------------------------------
# 2. 复查端口
#    只剩 TIME_WAIT 才算干净; 还有 LISTENING 就说明没清干净
# ---------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] 检查 $Port 端口有没有空出来" -ForegroundColor Cyan

$stillBusy = Get-PortListeners $Port

if ($stillBusy) {
    Write-Host "  端口 $Port 仍然被占用:" -ForegroundColor Red
    foreach ($s in $stillBusy) {
        Write-Host "      $($s.Address)   PID $($s.Pid)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host '  如果上面这个 PID 用下面这条命令查不到, 说明它是个"幽灵进程":' -ForegroundColor Yellow
    Write-Host "      Get-Process -Id <上面的PID>" -ForegroundColor DarkGray
    Write-Host "  这种一般是终端窗口被直接关掉、父进程先死留下的。两个办法:" -ForegroundColor Yellow
    Write-Host "      办法一: 关掉所有终端窗口, 或者重启电脑, 然后重新运行本脚本" -ForegroundColor Yellow
    Write-Host "      办法二: 换端口启动, 例如   .\重启服务.ps1 -Port 8001" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  已经停下, 不启动服务了(否则又会出现两个服务抢同一个端口)" -ForegroundColor Red
    exit 1
}

Write-Host "  端口干净, 可以启动" -ForegroundColor Green

# ---------------------------------------------------------------
# 3. 选择要启动的项目
# ---------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] 选择要启动的项目" -ForegroundColor Cyan

if ($AppDir -ne "") {
    $mainPy = Join-Path $AppDir "main.py"
    if (-not (Test-Path -LiteralPath $mainPy)) {
        Write-Host "  指定的目录里没有 main.py: $AppDir" -ForegroundColor Red
        exit 1
    }
    $chosen = (Resolve-Path -LiteralPath $AppDir).Path
    Write-Host "  使用命令行指定的目录" -ForegroundColor Green
}
else {
    # 在所有 day* 目录里找含 main.py 的文件夹, 按最近修改时间排序
    $dayDirs = Get-ChildItem -LiteralPath $RepoRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "day*" }

    $candidates = @()
    foreach ($d in $dayDirs) {
        $found = Get-ChildItem -LiteralPath $d.FullName -Recurse -Filter "main.py" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\(venv|\.venv|__pycache__|node_modules)\\' }
        $candidates += $found
    }
    $candidates = @($candidates | Sort-Object LastWriteTime -Descending)

    if ($candidates.Count -eq 0) {
        Write-Host "  没有找到任何 main.py" -ForegroundColor Red
        Write-Host "  可以用 -AppDir 参数直接指定项目目录" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "  找到了这些项目(最近改过的排在最前面):" -ForegroundColor Green
    for ($i = 0; $i -lt $candidates.Count; $i++) {
        $rel = $candidates[$i].FullName.Substring($RepoRoot.Length + 1)
        $tag = ""
        if ($i -eq 0) { $tag = "   <- 最近改过" }
        Write-Host ("     [{0}] {1}{2}" -f ($i + 1), $rel, $tag)
    }
    Write-Host ""
    $ans = Read-Host "  输入编号后回车(直接回车 = 1)"
    if ([string]::IsNullOrWhiteSpace($ans)) { $ans = "1" }

    $idx = 0
    if (-not [int]::TryParse($ans, [ref]$idx)) { $idx = 1 }
    if ($idx -lt 1 -or $idx -gt $candidates.Count) { $idx = 1 }

    $chosen = $candidates[$idx - 1].DirectoryName
}

# ---------------------------------------------------------------
# 4. 启动
# ---------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] 启动服务" -ForegroundColor Cyan
Write-Host "  项目目录: $chosen"
Write-Host "  使用解释器: $Python"
Write-Host "  端口: $Port"
Write-Host ""
Write-Host "  接口文档:   http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "  接口清单:   http://127.0.0.1:$Port/openapi.json" -ForegroundColor Green
Write-Host "              ^ 页面显示的接口和代码对不上时, 就看这个" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  启动后请留意控制台这两行:" -ForegroundColor DarkGray
Write-Host "     Application startup complete.    <- 应用起来了" -ForegroundColor DarkGray
Write-Host "     保存文件后出现 Reloading...        <- 新代码生效了" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  停止服务请按 Ctrl+C, 等回到命令行提示符再关窗口" -ForegroundColor DarkGray
Write-Host ""

Push-Location -LiteralPath $chosen
try {
    & $Python -m uvicorn main:app --reload --port $Port
}
finally {
    Pop-Location
}
