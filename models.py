from google.appengine.ext import db

# Models

class User(db.Model):
    username = db.StringProperty(required=True)
    password_digest = db.StringProperty(required=True)

    @classmethod
    def get_by(cls, key, value):
        return cls.gql("WHERE %s = :1" % key, value).get()

class Blog(db.Model):
    title = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    blog = db.TextProperty(required=True)
    author = db.ReferenceProperty(User, collection_name="blogs")

class Comment(db.Model):
    body = db.TextProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    author = db.ReferenceProperty(User, collection_name="comments")
    post = db.ReferenceProperty(Blog, collection_name="comments")

    @classmethod
    def by_post(cls, post_id):
        unsorted = filter(lambda x: x.post.key().id() == int(post_id), cls.all())
        if unsorted == []:
            return unsorted
        else:
            return sorted(unsorted, key=lambda x: x.date, reverse=True)

    @classmethod
    def by_author(cls, user_id):
        return filter(lambda x: x.user.key().id() == int(user_id), cls.all())

class Like(db.Model):
    user = db.ReferenceProperty(User, collection_name="likes", indexed=True)
    post = db.ReferenceProperty(Blog, collection_name="likes", indexed=True)
    status = db.BooleanProperty(required=True)

    @classmethod
    def count_likes(cls, post_id):
        all_votes = filter(lambda x: x.post.key().id() == int(post_id), cls.all())
        likes = filter(lambda x: x.status == True, all_votes)
        total_score = len(likes) - (len(all_votes) - len(likes))
        return total_score

    @classmethod
    def vote_of_post(cls, post, user):
        user_vote = filter(lambda x: x.post.key().id() == post.key().id() and x.user.username == user.username, cls.all())
        if len(user_vote) > 0:
            return user_vote[0].status
        else:
            return None
