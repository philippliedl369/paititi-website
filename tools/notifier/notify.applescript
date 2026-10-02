-- The thing that puts the banner on screen, and the only reason it exists is
-- the icon.
--
-- `osascript -e 'display notification'` works fine, but the banner carries
-- *Script Editor's* icon, because osascript is what delivered it — there is no
-- parameter to change that. A notification's icon is always the posting app's.
-- So the posting app has to be ours.
--
-- Compiled by build.sh into "Paititi Watch.app" with the Paititi dorje as its
-- icon. It reads the message from a file in /tmp rather than taking an
-- argument: `open -a` will not relaunch an app that is already running, and a
-- dropped argument would be a silently missing alert. /tmp also keeps this app
-- clear of TCC — it never reads ~/Desktop, so it needs no Full Disk Access,
-- unlike the Python that calls it.

--
-- Clicking a banner relaunches the app that posted it, so this runs for two
-- reasons and tells them apart by the message file: the watcher writes one
-- before every launch and this deletes it once shown. A message waiting means
-- "post it"; none means the banner was clicked, and the click opens the full
-- report the watcher left beside it. (Before this, a click re-posted the same
-- banner.)

on run
	set msgFile to "/tmp/paititi-watch-message.txt"
	set reportFile to "/tmp/paititi-watch-report.txt"
	try
		set msg to (do shell script "/bin/cat " & quoted form of msgFile & " && /bin/rm -f " & quoted form of msgFile)
	on error
		try
			do shell script "/bin/test -f " & quoted form of reportFile & " && /usr/bin/open " & quoted form of reportFile
		on error
			display notification "Retreat Guru check ran, but its message went missing." with title "paititi site"
		end try
		return
	end try
	display notification msg with title "paititi site"
end run
