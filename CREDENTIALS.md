# Credential cleanup

Two distinct MQTT passwords were committed in `tools/clients.json`. One was also
embedded in `tablet_website/src/javascript.js`. Do not reuse those values. The
firmware's historical password fields were empty; they are not a third known
exposed credential.

The cleanup removes the tracked credential configuration and replaces it with
examples and ignored local settings. Python reads credential values from named
environment variables. The tablet accepts credentials at runtime, and the
firmware uses an ignored local header. No replacement secret belongs in Git.

## Remaining owner action

The repository owner has not confirmed whether both exposed passwords have been
revoked or rotated. Before account transfer, the administrators responsible for
both MQTT accounts must confirm that the committed old values are no longer
usable. If an account or broker was retired, confirm that the corresponding
credential cannot authenticate anywhere it was reused. Do not post old or new
password values in issues, pull requests or this document.

No credentials were tested and no broker was contacted during cleanup. Deleting
current copies does not remove them from earlier commits, clones or forks. This
cleanup preserves Git history; it does not perform or imply a history rewrite.

The four project-specific permissions for team authority, institutional rules,
asset redistribution and SDK/binary redistribution including retained history
were confirmed by the owner on 22 October 2026. Credential revocation remains a
separate, unresolved transfer prerequisite.
