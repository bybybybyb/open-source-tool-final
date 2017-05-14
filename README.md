# open-source-tool-final

I tried to deploy onto GAE but there seems exist some problems on indexes which may still be generating. The deployed website on GAE is using UTC time.
RSS has been committed on the Experiment branch.


https://opensourcetoolproj-by653.appspot.com/

https://github.com/ylns1314/open-source-tool-final

## Structure
### HTML
  * index: the landing page with 3 different lists (all upcoming own reservations, all resources and my resources)
  * user: the profile page of a user showing all upcoming own reservations and own resources
  * reservation: detailed reservation page but seldom being used: most functions related to reservations have been embedded into the landing page
  * resource: detailed resource page with the reserve and the edit button
  * edit-resource: page used to create/edit a new resource
  * create-reservation: page used to create a new reservation
  * status: showing the operation status (whether success or fail for some reason) of edit-resource and create-reservation
 
### Third-party packages other than Django/Jinja2 that have been used
  * Bootstrap
  * JQuery
  * PyRSS2Gen
