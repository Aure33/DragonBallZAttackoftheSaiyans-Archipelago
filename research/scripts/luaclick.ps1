# Vrai double-clic sur une ligne de la liste des scripts de la console Lua de BizHawk,
# puis retour de la fenêtre active et de la souris à leur état d'avant. Usage : luaclick.ps1 <ligne 1-based>
param([int]$row = 3, [string]$mode = "double")
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class C {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, IntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, IntPtr e);
  public struct RECT { public int L, T, R, B; }
  public struct POINT { public int X, Y; }
  public static IntPtr Find(uint pid, string title) { IntPtr r = IntPtr.Zero; EnumWindows((h, p) => { uint q; GetWindowThreadProcessId(h, out q); var s = new StringBuilder(256); GetWindowText(h, s, 256); if (q == pid && s.ToString() == title) r = h; return true; }, IntPtr.Zero); return r; }
}
"@
$lua = [C]::Find((Get-Process EmuHawk).Id, "Lua Console")
if ($lua -eq [IntPtr]::Zero) { Write-Output "console Lua introuvable"; exit 1 }
$before = [C]::GetForegroundWindow()
$mouse = New-Object C+POINT; [void][C]::GetCursorPos([ref]$mouse)
$r = New-Object C+RECT; [void][C]::GetWindowRect($lua, [ref]$r)
[C]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [C]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)  # Alt : autorise le changement de fenêtre active
[void][C]::SetForegroundWindow($lua); Start-Sleep -Milliseconds 250
if ($mode -eq "toggle") {
  # sélectionner la ligne, puis le bouton « Toggle Script » (coche verte) de la barre d'outils
  [void][C]::SetCursorPos($r.L + 60, $r.T + 101 + 20 + ($row - 1) * 14); Start-Sleep -Milliseconds 120
  [C]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [C]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 200
  [void][C]::SetCursorPos($r.L + 74, $r.T + 67); Start-Sleep -Milliseconds 120
  [C]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [C]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero)
} else {
  [void][C]::SetCursorPos($r.L + 60, $r.T + 101 + 20 + ($row - 1) * 14); Start-Sleep -Milliseconds 120
  foreach ($i in 1, 2) { [C]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [C]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero) }
}
Start-Sleep -Milliseconds 400
[void][C]::SetCursorPos($mouse.X, $mouse.Y)
[C]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [C]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)
[void][C]::SetForegroundWindow($before)
Write-Output "double-clic fait sur la ligne $row"
