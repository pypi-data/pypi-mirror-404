from rest_framework import serializers

from content_studio.settings import cs_settings


class MediaItemSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = cs_settings.MEDIA_LIBRARY_MODEL
        fields = "__all__"

    def get_thumbnail(self, obj):
        admin_site = cs_settings.ADMIN_SITE

        if admin_site and obj.type == "image":
            return admin_site.get_thumbnail(obj)

        return None


class MediaFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = cs_settings.MEDIA_LIBRARY_FOLDER_MODEL
        fields = ["id", "name", "parent"]
