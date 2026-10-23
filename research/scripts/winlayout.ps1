# Remet la console Lua de BizHawk au premier plan (restaurée) et réduit la fenêtre du jeu, sans rien fermer.
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class WL {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  public static Dictionary<string, IntPtr> Of(uint pid) { var d = new Dictionary<string, IntPtr>(); EnumWindows((h, p) => { uint q; GetWindowThreadProcessId(h, out q); var s = new StringBuilder(256); GetWindowText(h, s, 256); if (q == pid && s.Length > 0) d[s.ToString()] = h; return true; }, IntPtr.Zero); return d; }
}
"@
$w = [WL]::Of((Get-Process EmuHawk).Id)
foreach ($k in $w.Keys) {
  if ($k -eq "Lua Console") { [void][WL]::ShowWindow($w[$k], 6); Start-Sleep -Milliseconds 300; [void][WL]::ShowWindow($w[$k], 1) }  # réduire puis SW_SHOWNORMAL
  elseif ($k -like "*BizHawk*") { [void][WL]::ShowWindow($w[$k], 6) }  # SW_MINIMIZE
}
Write-Output "ok"
