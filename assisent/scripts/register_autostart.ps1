$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$project = Split-Path -Parent $root
$python = Join-Path $project "venv\Scripts\python.exe"
$script = Join-Path $project "manage_service.py"
$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" monitor" -WorkingDirectory $project
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType Interactive -RunLevel LeastPrivilege
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Description "AI Partner Chat 后端监控与自启动"
Register-ScheduledTask -TaskName "AIPartnerChatServer" -InputObject $task -Force
Write-Host "已注册计划任务：AIPartnerChatServer"