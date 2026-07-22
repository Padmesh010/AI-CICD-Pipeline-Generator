class CostEstimator:
    def __init__(self):
        pass

    def estimate(self, language, target_platform, cloud_provider="AWS", instances=2):
        """Estimate pipeline build times and cloud operational costs."""
        # 1. Build Time Estimation (in seconds)
        base_times = {
            "python": 120,
            "nodejs": 180,
            "node.js": 180,
            "java": 240,
            "go": 90,
            "rust": 480,
            "php": 110
        }
        
        lang_key = language.lower()
        build_time = base_times.get(lang_key, 150)
        
        # 2. Cloud Cost Estimation (monthly)
        cloud_lower = cloud_provider.lower()
        if "aws" in cloud_lower:
            vm_unit = 25.00 # t3.medium
            alb_unit = 22.00
            rds_unit = 18.00
            storage_unit = 0.10 # per GB
            provider_name = "Amazon Web Services (AWS)"
        elif "gcp" in cloud_lower:
            vm_unit = 22.00 # e2-medium
            alb_unit = 18.00
            rds_unit = 15.00
            storage_unit = 0.08
            provider_name = "Google Cloud Platform (GCP)"
        elif "azure" in cloud_lower:
            vm_unit = 26.00 # B2s
            alb_unit = 20.00
            rds_unit = 19.00
            storage_unit = 0.09
            provider_name = "Microsoft Azure"
        else:
            vm_unit = 15.00
            alb_unit = 0.00
            rds_unit = 10.00
            storage_unit = 0.05
            provider_name = "On-Premises / VPS"

        vm_total = vm_unit * instances
        rds_total = rds_unit
        storage_total = storage_unit * 50 # Assume 50GB storage
        alb_total = alb_unit
        monthly_cost = vm_total + rds_total + storage_total + alb_total

        # 3. Optimization suggestions
        suggestions = []
        if build_time > 180:
            suggestions.append("Optimize build duration: Implement step cache for dependencies (npm ci cache, pip Cache).")
        suggestions.append("Reduce registry costs: Configure automatic image tag retention rules to prune tags older than 30 days.")
        if "aws" in cloud_lower:
            suggestions.append("Compute savings: Utilize AWS Spot Instances for non-critical developer environments (saves up to 70%).")
        elif "gcp" in cloud_lower:
            suggestions.append("Compute savings: Configure Preemptible VMs for automated testing node groups.")
        suggestions.append(f"Auto-scaling: Deploy a Horizontal Pod Autoscaler (HPA) to scale replica counts between 1 and 5 rather than keeping {instances} nodes static.")

        return {
            "build_time_sec": build_time,
            "build_time_display": f"{build_time // 60}m {build_time % 60}s",
            "cloud_provider": provider_name,
            "compute_cost": vm_total,
            "database_cost": rds_total,
            "load_balancer_cost": alb_total,
            "storage_cost": storage_total,
            "monthly_cost": monthly_cost,
            "monthly_cost_display": f"${monthly_cost:.2f}/mo",
            "suggestions": suggestions
        }

# Global cost estimator instance
cost_estimator = CostEstimator()
