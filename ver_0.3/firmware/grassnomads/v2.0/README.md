
idea:

wakeup

read previous data line.

if last attempt was a failure, then try to send now, marking time and date and whether successful.

if the last attempt was successful, then:

check the time.  if it's currently 5 AM or 1 PM:

if we're in the same hour as the last recorded send, don't send again; go back to sleep.  

if we're not in the same hour, then send, marking time and date and whether successful (1 or )

