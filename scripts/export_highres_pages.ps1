<#
.SYNOPSIS
  用本机 PowerPoint COM 把导出的 pptx 矢量渲染成高清整页 PNG（默认 1920x1080），
  作为讲解视频的画面源。飞书 +screenshot 只出 960x540，放大到 1080p 会发虚，
  视频画面请改用本脚本从 pptx 原生矢量导出。

.DESCRIPTION
  Windows only（依赖本机安装的 PowerPoint / Office）。
  自动把含中文或空格的 pptx 复制成临时英文副本再 Open，规避 COM 0x8007007B 路径报错；
  导出完成后清理临时副本。

.PARAMETER Pptx
  导出的 .pptx 绝对路径或相对路径。

.PARAMETER OutDir
  高清页图输出目录（不存在会自动创建）。

.PARAMETER Width
  导出宽度像素，默认 1920。

.PARAMETER Height
  导出高度像素，默认 1080。

.PARAMETER Prefix
  输出文件名前缀，默认 p，生成 p1.png p2.png ...

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File export_highres_pages.ps1 `
    -Pptx ".\out\deck.pptx" -OutDir ".\highres"
#>
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Width = 1920,
    [int]$Height = 1080,
    [string]$Prefix = "p"
)

$ErrorActionPreference = "Stop"

# 解析绝对路径
$pptxPath = (Resolve-Path -LiteralPath $Pptx -ErrorAction Stop).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$outDirAbs = (Resolve-Path -LiteralPath $OutDir).Path

# 临时英文副本：COM 对中文/非 ASCII 路径 Open 会报 0x8007007B
$tmp = Join-Path $env:TEMP ("hr_src_{0}.pptx" -f ([guid]::NewGuid().ToString("N")))
Copy-Item -LiteralPath $pptxPath -Destination $tmp -Force

$ppt = $null
$pres = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    # Open(FileName, ReadOnly=msoTrue(-1), Untitled=msoFalse(0), WithWindow=msoFalse(0))
    $pres = $ppt.Presentations.Open($tmp, -1, 0, 0)
    $count = $pres.Slides.Count
    Write-Output ("SLIDES={0}  target={1}x{2}" -f $count, $Width, $Height)

    for ($i = 1; $i -le $count; $i++) {
        $target = Join-Path $outDirAbs ("{0}{1}.png" -f $Prefix, $i)
        $pres.Slides.Item($i).Export($target, "PNG", $Width, $Height)
        if (Test-Path -LiteralPath $target) {
            $kb = [math]::Round((Get-Item -LiteralPath $target).Length / 1KB)
            Write-Output ("P{0} -> {1} ({2} KB)" -f $i, $target, $kb)
        } else {
            Write-Output ("P{0} EXPORT_FAILED" -f $i)
        }
    }
}
finally {
    if ($pres -ne $null) { try { $pres.Close() } catch {} }
    if ($ppt -ne $null) {
        try { $ppt.Quit() } catch {}
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue }
}
