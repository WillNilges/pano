I need the format for the panoramas

I think it was nnXXX.jpg or XXX.jpg

I want an API route that can be used to upload panoramas, and they'll get sent to both dropbox and minio. I think that would be simpler and better than trying to rely wholly on dropbox.

That said, at some point I am going to want dropbox webhooks, to notify me if anyone changes anything.

Wait what if I just used dropbox for backups. Would that work?

I think that's impractical because of how large the dataset is.

Incremental backups might work. I was under the assumption that dropbox would be the source of truth. I thiiiink it still should be, but that introduces a lot of complexity.

How about this: Instead of reaching out directly to S3, and having to keep MeshDB up to date, we make meshdb make requests to Pano? Would that be performant? Would that work?

I want Pano to be stateless, but if Dropbox and Minio get out of sync, that's a problem. Maybe it's premature optimization to think about it right now.

---

Let's use MeshDB as the source of truth. When we do the big import, we'll shove everything into Dropbox, and then we can port the logic over from MeshDB into pano to do a "sweep" of Dropbox and sync everything over. That will take a while, but we should only have to do it in the event of disaster. We'll rely on the titles of the files in Dropbox as the ultimate source of truth. Pano, however, will rely on MeshDB's recollection of the panoramas per building/install/whatever. If there's a "miss" in S3, Pano can quietly try to re-sync it in the background.

I definitely still want the concept of an abstract storage class. I can make a "local" one to mock Dropbox for now.

I wonder if I can make meshdb use a configurable pano URL.... hmmmm. Probably too much work.
