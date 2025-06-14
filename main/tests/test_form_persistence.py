"""
Tests for order form persistence functionality.
"""

from django.test import Client, TestCase, override_settings

from main.models import FactoryMachineDefinition, Project


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class FormPersistenceTestCase(TestCase):
    """Test form persistence using localStorage simulation."""

    def setUp(self):
        """Set up test client and test data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for persistence testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512, "enable_safety_checker": False},
            is_active=True,
        )
        self.test_project = Project.objects.create(
            name="Test Project", description="Test project for persistence", status="active"
        )

    def test_form_persistence_javascript_structure(self):
        """Test that form persistence JavaScript has proper structure and functions."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Test that saveFormValues function captures all form fields (updated syntax)
        self.assertIn("machine: machineField?.value || ''", content)
        self.assertIn("prompt: promptField?.value || ''", content)
        self.assertIn("negative_prompt: negativePromptField?.value || ''", content)
        self.assertIn("title: document.getElementById('title')?.value || ''", content)
        self.assertIn("project: document.getElementById('project')?.value || ''", content)
        self.assertIn("generationCount: document.getElementById('generationCount')?.value || '1'", content)
        self.assertIn("batchSize: document.getElementById('batchSize')?.value || '4'", content)

        # Test that localStorage operations are present
        self.assertIn("localStorage.setItem('orderFormData'", content)
        self.assertIn("localStorage.getItem('orderFormData')", content)

        # Test that loadFormValues restores fields (updated syntax with null checks)
        self.assertIn("machineField.value = formData.machine", content)
        self.assertIn("promptField.value = formData.prompt", content)
        self.assertIn("projectField.value = formData.project", content)

    def test_form_persistence_event_listeners(self):
        """Test that event listeners are properly attached for form persistence."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Check that event listeners are attached to form fields
        self.assertIn("element.addEventListener('change', saveFormValues)", content)
        self.assertIn("element.addEventListener('input', saveFormValues)", content)

        # Check that specific fields have event listeners
        self.assertIn("batchSizeElement.addEventListener('change'", content)
        self.assertIn("generationCountElement.addEventListener('input'", content)

        # Check that the form fields array includes all expected fields
        self.assertIn("['machine', 'prompt', 'negative_prompt', 'title', 'project']", content)

    def test_form_persistence_advanced_parameters(self):
        """Test that advanced parameters are included in persistence."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Test that advanced parameters are saved
        self.assertIn("#advancedParams input, #advancedParams select", content)
        self.assertIn("advancedParams[input.name] = input.value", content)
        self.assertIn("formData.advancedParams = advancedParams", content)

        # Test that advanced parameters are restored
        self.assertIn("formData.advancedParams", content)
        self.assertIn("setTimeout(() => {", content)  # Advanced params restored with delay

    def test_form_persistence_initialization_sequence(self):
        """Test that form persistence initialization happens in correct sequence."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Find positions of key initialization steps
        load_page_data_pos = content.find("if (typeof loadPageData === 'function')")
        load_form_values_pos = content.find("if (typeof loadFormValues === 'function')")
        form_submit_pos = content.find("form.addEventListener('submit'")

        # Verify correct order: loadPageData -> loadFormValues -> form submit handler
        self.assertLess(load_page_data_pos, load_form_values_pos, "loadPageData should be called before loadFormValues")
        self.assertLess(load_form_values_pos, form_submit_pos, "loadFormValues should be called before form submit handler")

    def test_clear_form_functionality(self):
        """Test that explicit form clearing works (via Clear button only)."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Check that clear form function exists and removes data
        # But only in the explicit clearForm() function, not on successful submission
        self.assertIn("clearForm", content)

        # Find the clearForm function
        clear_form_start = content.find("window.clearForm")
        self.assertGreater(clear_form_start, 0)

        # localStorage.removeItem should only be in clearForm function
        # Not in submission success handlers
        self.assertIn("localStorage.removeItem('orderFormData')", content[clear_form_start : clear_form_start + 1000])

    def test_form_persistence_error_handling(self):
        """Test that form persistence has proper error handling."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Check that JSON parsing has error handling
        self.assertIn("try {", content)
        self.assertIn("} catch (e) {", content)
        self.assertIn("console.error('Error loading saved form data:'", content)

    def test_machine_selection_triggers_parameter_loading(self):
        """Test that machine selection triggers parameter loading after persistence restore."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # When machine is restored, it should trigger change event to load parameters
        self.assertIn("machineField.dispatchEvent(new Event('change'))", content)

    def test_total_products_calculation_after_restore(self):
        """Test that total products is recalculated after form values are restored."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # updateTotalProducts should be called after restoring values
        self.assertIn("updateTotalProducts()", content)

        # Check that the function exists and updates the display
        self.assertIn("function updateTotalProducts()", content)
        self.assertIn("totalEl.textContent = totalProducts", content)

    def test_negative_prompt_persistence_preservation(self):
        """Test that negative_prompt values are preserved during machine parameter loading."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Test that negative_prompt is excluded from dynamic parameter generation
        self.assertIn("if (key === 'prompt' || key === 'negative_prompt' || key === 'title') continue;", content)

        # Test that existing values are preserved before clearing dynamic parameters
        self.assertIn("Preserve existing values before clearing", content)
        self.assertIn("#negative_prompt", content)

        # Test that values are restored after parameter generation
        self.assertIn("Restoring ${fieldId}:", content)
        self.assertIn("Values restored after parameter generation", content)
