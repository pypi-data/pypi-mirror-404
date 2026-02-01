from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import declarative_base, Session
from typing import Optional

Base = declarative_base()


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True)
    azure_oid = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    profile_image = Column(String(1024), nullable=True)  # URL or path to image
    additional_info = Column(Text, nullable=True)  # JSON or text blob for extras
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class UserProfileManager:
    """
    Handles retrieval and persistence of user profiles, merging Microsoft 365 SSO info
    with locally stored additional data (e.g., profile images).
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_or_create(self, ms_info: dict) -> UserProfile:
        """
        Retrieves a UserProfile by Azure OID; if not found, creates one.
        The ms_info should contain keys: 'oid', 'email', 'name', optional 'profile_image'.
        """
        oid = ms_info.get('oid')
        user = self.db.query(UserProfile).filter_by(azure_oid=oid).one_or_none()
        if not user:
            user = UserProfile(
                azure_oid=oid,
                email=ms_info.get('email'),
                name=ms_info.get('name'),
                profile_image=ms_info.get('profile_image')
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        # Update core fields if changed
        changed = False
        if user.email != ms_info.get('email'):
            user.email = ms_info.get('email')
            changed = True
        if user.name != ms_info.get('name'):
            user.name = ms_info.get('name')
            changed = True

        # If MS provides an image, override; else keep existing
        ms_image = ms_info.get('profile_image')
        if ms_image and user.profile_image != ms_image:
            user.profile_image = ms_image
            changed = True

        if changed:
            self.db.commit()
            self.db.refresh(user)
        return user

    def get_profile_image(self, azure_oid: str) -> Optional[str]:
        """
        Returns the profile image URL/path for the given user.
        """
        user = self.db.query(UserProfile).filter_by(azure_oid=azure_oid).one_or_none()
        return user.profile_image if user else None
