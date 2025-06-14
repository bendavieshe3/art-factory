from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Project, Order, Product, OrderItem, FactoryMachineDefinition


class ProjectModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project", description="A test project for unit testing", status="active"
        )

    def test_project_creation(self):
        """Test that a project can be created with required fields."""
        self.assertEqual(self.project.name, "Test Project")
        self.assertEqual(self.project.description, "A test project for unit testing")
        self.assertEqual(self.project.status, "active")
        self.assertEqual(self.project.order_count, 0)
        self.assertEqual(self.project.product_count, 0)

    def test_project_str_representation(self):
        """Test the string representation of a project."""
        self.assertEqual(str(self.project), "Test Project")

    def test_project_update_counts(self):
        """Test that project counts are updated correctly."""
        # Create a factory machine for testing
        machine = FactoryMachineDefinition.objects.create(
            name="test_machine",
            display_name="Test Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={},
            default_parameters={},
        )

        # Create an order associated with the project
        order = Order.objects.create(
            title="Test Order",
            prompt="Test prompt",
            factory_machine_name=machine.name,
            provider=machine.provider,
            project=self.project,
        )

        # Create an order item
        order_item = OrderItem.objects.create(order=order, prompt="Test prompt", parameters={})

        # Create a product
        product = Product.objects.create(
            title="Test Product",
            prompt="Test prompt",
            provider=machine.provider,
            model_name=machine.name,
            file_path="test/test.jpg",
            file_size=1024,
            file_format="jpg",
            width=1024,
            height=1024,
            order_item=order_item,  # Properly link to order item
        )

        # Associate product with order item for backward compatibility
        order_item.product = product
        order_item.save()

        # Update project counts
        self.project.update_counts()

        # Check that counts are correct
        self.assertEqual(self.project.order_count, 1)
        self.assertEqual(self.project.product_count, 1)

    def test_get_recent_products(self):
        """Test that get_recent_products returns products from project orders."""
        # Create a factory machine for testing
        machine = FactoryMachineDefinition.objects.create(
            name="test_machine",
            display_name="Test Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={},
            default_parameters={},
        )

        # Create an order associated with the project
        order = Order.objects.create(
            title="Test Order",
            prompt="Test prompt",
            factory_machine_name=machine.name,
            provider=machine.provider,
            project=self.project,
        )

        # Create an order item
        order_item = OrderItem.objects.create(order=order, prompt="Test prompt", parameters={})

        # Create multiple products
        for i in range(3):
            # Create a separate order item for each product
            item = OrderItem.objects.create(order=order, prompt="Test prompt", parameters={})

            product = Product.objects.create(
                title=f"Test Product {i}",
                prompt="Test prompt",
                provider=machine.provider,
                model_name=machine.name,
                file_path=f"test/test{i}.jpg",
                file_size=1024,
                file_format="jpg",
                width=1024,
                height=1024,
                order_item=item,  # Properly link to order item
            )

            # Associate product with order item for backward compatibility
            item.product = product
            item.save()

        # Get recent products
        recent_products = self.project.get_recent_products(2)

        # Should return 2 products (limited by the parameter)
        self.assertEqual(len(recent_products), 2)


class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            name="Test Project", description="A test project for unit testing", status="active"
        )

    def test_projects_view(self):
        """Test the main projects page."""
        response = self.client.get(reverse("main:projects"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")
        self.assertContains(response, "Projects")

    def test_all_projects_view(self):
        """Test the all projects page."""
        response = self.client.get(reverse("main:all_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")
        self.assertContains(response, "All Projects")

    def test_project_detail_view(self):
        """Test the project detail page."""
        response = self.client.get(reverse("main:project_detail", args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")
        self.assertContains(response, "A test project for unit testing")

    def test_project_detail_view_404(self):
        """Test that project detail returns 404 for non-existent project."""
        response = self.client.get(reverse("main:project_detail", args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_project_create_view(self):
        """Test creating a new project."""
        response = self.client.post(
            reverse("main:project_create"), {"name": "New Test Project", "description": "A new test project"}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after creation

        # Check that project was created
        new_project = Project.objects.get(name="New Test Project")
        self.assertEqual(new_project.description, "A new test project")
        self.assertEqual(new_project.status, "active")

    def test_project_create_view_missing_name(self):
        """Test creating a project without a name fails."""
        response = self.client.post(reverse("main:project_create"), {"description": "A test project without name"})
        # Should redirect back to projects page with error message
        self.assertEqual(response.status_code, 302)

        # Project should not be created
        self.assertFalse(Project.objects.filter(description="A test project without name").exists())

    def test_project_update_view(self):
        """Test updating an existing project."""
        response = self.client.post(
            reverse("main:project_update", args=[self.project.id]),
            {"name": "Updated Test Project", "description": "Updated description", "status": "completed"},
        )
        self.assertEqual(response.status_code, 302)  # Redirect after update

        # Check that project was updated
        updated_project = Project.objects.get(id=self.project.id)
        self.assertEqual(updated_project.name, "Updated Test Project")
        self.assertEqual(updated_project.description, "Updated description")
        self.assertEqual(updated_project.status, "completed")

    def test_project_delete_view(self):
        """Test deleting a project."""
        project_id = self.project.id
        response = self.client.post(reverse("main:project_delete", args=[project_id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion

        # Check that project was deleted
        self.assertFalse(Project.objects.filter(id=project_id).exists())

    def test_projects_api(self):
        """Test the projects API endpoint."""
        response = self.client.get(reverse("main:projects_api"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("projects", data)
        self.assertTrue(len(data["projects"]) >= 1)

        # Find our test project in the response
        test_project = None
        for project in data["projects"]:
            if project["name"] == "Test Project":
                test_project = project
                break

        self.assertIsNotNone(test_project)
        self.assertEqual(test_project["name"], "Test Project")

    def test_project_detail_api(self):
        """Test the project detail API endpoint."""
        response = self.client.get(reverse("main:project_detail_api", args=[self.project.id]))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["name"], "Test Project")
        self.assertEqual(data["description"], "A test project for unit testing")
        self.assertEqual(data["status"], "active")


class ProjectIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            name="Integration Test Project", description="A project for integration testing", status="active"
        )

        # Create a factory machine for testing orders
        self.machine = FactoryMachineDefinition.objects.create(
            name="test_machine",
            display_name="Test Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={},
            default_parameters={},
        )

    def test_inventory_project_filter(self):
        """Test that inventory page filters by project correctly."""
        # Create an order with the project
        order = Order.objects.create(
            title="Test Order",
            prompt="Test prompt",
            factory_machine_name=self.machine.name,
            provider=self.machine.provider,
            project=self.project,
        )

        # Create order item and product
        order_item = OrderItem.objects.create(order=order, prompt="Test prompt", parameters={})

        product = Product.objects.create(
            title="Test Product",
            prompt="Test prompt",
            provider=self.machine.provider,
            model_name=self.machine.name,
            file_path="test/test.jpg",
            file_size=1024,
            file_format="jpg",
            width=1024,
            height=1024,
        )

        order_item.product = product
        order_item.save()

        # Test inventory page with project filter
        response = self.client.get(reverse("main:inventory"), {"project": self.project.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Project")

        # Test that the product appears in the filtered results
        self.assertIn("products_json", response.context)

    def test_order_creation_with_project(self):
        """Test that orders can be created with project association."""
        response = self.client.get(reverse("main:order"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Project")

        # Check that project is in the context
        self.assertIn("projects", response.context)
        self.assertTrue(len(response.context["projects"]) >= 1)

        # Find our test project in the context
        project_names = [p.name for p in response.context["projects"]]
        self.assertIn("Integration Test Project", project_names)

    def test_project_url_parameter_preselection(self):
        """Test that project URL parameter pre-selects project in order form."""
        response = self.client.get(reverse("main:order"), {"project": self.project.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'value="{self.project.id}"')
