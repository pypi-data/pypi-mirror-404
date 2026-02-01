from saas.drf.serializers import FlattenModelSerializer
from saas.identity.serializers.user import SimpleUserSerializer
from saas.tenancy.models import Member
from saas.test import SaasTestCase


class MemberSerializer(FlattenModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Member
        fields = '__all__'
        flatten_fields = ['user']


class TestModelSerializer(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID

    def test_flatten_fields(self):
        user = self.get_user()
        user.first_name = 'Django'
        user.save()
        member = Member.objects.get(user=user, tenant_id=self.tenant_id)
        serializer = MemberSerializer(member)
        self.assertEqual(serializer.data['name'], 'Django')
