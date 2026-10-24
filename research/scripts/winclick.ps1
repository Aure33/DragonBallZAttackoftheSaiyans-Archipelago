# Clique dans une fenêtre d'un processus (coordonnées relatives à la fenêtre), puis tape éventuellement du texte.
# La fenêtre passe au premier plan le temps de l'action. Ex. : winclick.ps1 -Name poptracker -X 202 -Y 48 -Text "localhost:38281{ENTER}"
param([string]$Name, [int]$X, [int]$Y, [string]$Text = "", [string]$Title = "")
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class C {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, IntPtr e);
  public struct RECT { public int L, T, R, B; }
  public static List<IntPtr> Of(uint pid) { var l = new List<IntPtr>(); EnumWindows((h, p) => { uint q; GetWindowThreadProcessId(h, out q); if (q == pid && IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero); return l; }
}
"@
$p = (Get-Process $Name).Id
foreach ($h in [C]::Of($p)) {
  $s = New-Object System.Text.StringBuilder 256; [void][C]::GetWindowText($h, $s, 256)
  if ($Title -and -not $s.ToString().Contains($Title)) { continue }
  $r = New-Object C+RECT; [void][C]::GetWindowRect($h, [ref]$r)
  if (($r.R - $r.L) -lt 50) { continue }
  [void][C]::SetForegroundWindow($h); Start-Sleep -Milliseconds 300
  [void][C]::SetCursorPos($r.L + $X, $r.T + $Y); Start-Sleep -Milliseconds 100
  [C]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [C]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero)
  if ($Text) { Start-Sleep -Milliseconds 500; [System.Windows.Forms.SendKeys]::SendWait($Text) }
  Write-Output "clic dans « $($s.ToString()) » en ($X, $Y)"
  break
}
