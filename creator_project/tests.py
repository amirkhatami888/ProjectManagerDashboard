from django.test import TestCase
from django.contrib.auth import get_user_model
from .forms import FundingRequestForm, ExpertFundingReviewForm
from .models import Project, FundingRequest
from creator_program.models import Program

# Create your tests here.

class FundingRequestFormTest(TestCase):
    def setUp(self):
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create a test program
        self.program = Program.objects.create(
            title='Test Program',
            program_type='عملیات عمرانی',
            province='تهران',
            city='تهران',
            created_by=self.user
        )
        
        # Create a test project
        self.project = Project.objects.create(
            program=self.program,
            name='Test Project',
            project_type='عملیات عمرانی',
            province='تهران',
            city='تهران',
            created_by=self.user
        )
    
    def test_funding_request_form_with_user(self):
        """Test that FundingRequestForm can be initialized with user parameter"""
        # This should not raise an error
        form = FundingRequestForm(user=self.user)
        self.assertIsNotNone(form)
        
    def test_funding_request_form_without_user(self):
        """Test that FundingRequestForm can be initialized without user parameter"""
        # This should not raise an error
        form = FundingRequestForm()
        self.assertIsNotNone(form)
    
    def test_funding_request_form_currency_input(self):
        """Test that FundingRequestForm handles comma-formatted currency input correctly"""
        # Test with comma-formatted amount
        form_data = {
            'project': self.project.id,
            'province_suggested_amount': '51,486',
            'priority': 'متوسط',
            'province_description': 'Test description'
        }
        form = FundingRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['province_suggested_amount'], 51486)
    
    def test_funding_request_form_invalid_currency_input(self):
        """Test that FundingRequestForm handles invalid currency input correctly"""
        # Test with invalid amount
        form_data = {
            'project': self.project.id,
            'province_suggested_amount': 'invalid',
            'priority': 'متوسط',
            'province_description': 'Test description'
        }
        form = FundingRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('province_suggested_amount', form.errors)
    
    def test_funding_request_form_save(self):
        """Test that FundingRequestForm can save data correctly"""
        # Test with valid data
        form_data = {
            'project': self.project.id,
            'province_suggested_amount': '51,486',
            'priority': 'متوسط',
            'province_description': 'Test description'
        }
        form = FundingRequestForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Save the form
        funding_request = form.save(commit=False)
        funding_request.created_by = self.user
        funding_request.save()
        
        # Verify the data was saved correctly
        self.assertEqual(funding_request.province_suggested_amount, 51486)
        self.assertEqual(funding_request.project, self.project)
        self.assertEqual(funding_request.priority, 'متوسط')
        self.assertEqual(funding_request.province_description, 'Test description')
    
    def test_expert_review_form_approve(self):
        """Test that ExpertFundingReviewForm can approve funding requests"""
        # Create a funding request for testing
        funding_request = FundingRequest.objects.create(
            project=self.project,
            created_by=self.user,
            province_suggested_amount=50000,
            priority='متوسط',
            province_description='Test description',
            status='ارسال شده به کارشناس'
        )
        
        # Test approval
        form_data = {
            'headquarters_suggested_amount': '45,000',
            'expert_description': 'تایید می‌شود',
            'action': 'approve',
            'expert_rejection_reason': ''
        }
        form = ExpertFundingReviewForm(data=form_data, instance=funding_request)
        self.assertTrue(form.is_valid())
    
    def test_expert_review_form_reject(self):
        """Test that ExpertFundingReviewForm can reject funding requests"""
        # Create a funding request for testing
        funding_request = FundingRequest.objects.create(
            project=self.project,
            created_by=self.user,
            province_suggested_amount=50000,
            priority='متوسط',
            province_description='Test description',
            status='ارسال شده به کارشناس'
        )
        
        # Test rejection with reason
        form_data = {
            'headquarters_suggested_amount': '0',
            'expert_description': 'رد می‌شود',
            'action': 'reject',
            'expert_rejection_reason': 'مبلغ درخواستی بیش از حد مجاز است'
        }
        form = ExpertFundingReviewForm(data=form_data, instance=funding_request)
        self.assertTrue(form.is_valid())
    
    def test_expert_review_form_reject_without_reason(self):
        """Test that ExpertFundingReviewForm requires rejection reason when rejecting"""
        # Create a funding request for testing
        funding_request = FundingRequest.objects.create(
            project=self.project,
            created_by=self.user,
            province_suggested_amount=50000,
            priority='متوسط',
            province_description='Test description',
            status='ارسال شده به کارشناس'
        )
        
        # Test rejection without reason (should fail)
        form_data = {
            'headquarters_suggested_amount': '0',
            'expert_description': 'رد می‌شود',
            'action': 'reject',
            'expert_rejection_reason': ''
        }
        form = ExpertFundingReviewForm(data=form_data, instance=funding_request)
        self.assertFalse(form.is_valid())
        self.assertIn('expert_rejection_reason', form.errors)
