
class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    name = Column(String)

    mobile = Column(String)

    created_at = Column(DateTime)

class Chat(Base):

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)

    question = Column(Text)

    answer = Column(Text)

    created_at = Column(DateTime)

class File(Base):

    __tablename__ = "files"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)

    filename = Column(String)

    path = Column(String)

    file_type = Column(String)