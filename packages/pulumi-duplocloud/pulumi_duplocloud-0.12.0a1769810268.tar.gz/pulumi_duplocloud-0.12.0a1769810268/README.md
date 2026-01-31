# DuploCloud Resource Provider

The DuploCloud Resource Provider lets you manage [DuploCloud](https://duplocloud.com/) resources.

## Installing

The DuploCloud provider is available as a package in all Pulumi languages:

* JavaScript/TypeScript: [`@duplocloud/pulumi`](https://www.npmjs.com/package/@duplocloud/pulumi)
* Python: [`pulumi-duplocloud`](https://pypi.org/project/pulumi-duplocloud/)
* Go: [`github.com/duplocloud/pulumi-duplocloud/sdk/go/duplocloud`](https://github.com/duplocloud/pulumi-duplocloud)
* .NET: [`DuploCloud.Pulumi`](https://www.nuget.org/packages/DuploCloud.Pulumi/)

### Node.js (JavaScript/TypeScript)

To use from JavaScript or TypeScript in Node.js, install using either `npm`:

```bash
npm install @duplocloud/pulumi
```

or `yarn`:

```bash
yarn add @duplocloud/pulumi
```

### Python

To use from Python, install using `pip`:

```bash
pip install pulumi-duplocloud
```

### Go

To use from Go, use `go get` to grab the latest version of the library:

```bash
go get github.com/duplocloud/pulumi-duplocloud/sdk/go/...
```

### C#

To use from .NET, install using `dotnet add package`:

```bash
dotnet add package DuploCloud.Pulumi
```

### Provider Binary

For local development or specific version requirements, you can install the provider plugin directly:

```bash
pulumi plugin install resource duplocloud --server github://api.github.com/duplocloud/pulumi-duplocloud
```

To install a specific version:

```bash
pulumi plugin install resource duplocloud v0.0.1 --server github://api.github.com/duplocloud/pulumi-duplocloud
```

## Configuration

The DuploCloud provider requires the following configuration parameters:

- `duplocloud:duploHost` - Base URL to the DuploCloud REST API
- `duplocloud:duploToken` - Bearer token for authentication

You can set these using environment variables:

```bash
export duplo_host="https://your-duplocloud-instance.com"
export duplo_token="<your_duplo_token>"
```

## Example usage

An example demonstrating the deployment of DuploCloud infrastructure, tenant, EKS node, and web application on Kubernetes using the DuploCloud Pulumi provider across multiple language SDKs.

### Go

```golang
package main

import (
	"github.com/duplocloud/pulumi-duplocloud/sdk/go/duplocloud"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		// Set up the infrastructure.

		infra, err := duplocloud.NewInfrastructure(ctx, "infra", &duplocloud.InfrastructureArgs{
			InfraName:       pulumi.String("pulumi-infra"),
			Cloud:           pulumi.Int(0),
			Region:          pulumi.String("us-east-2"),
			Azcount:         pulumi.Int(2),
			SubnetCidr:      pulumi.Int(24),
			EnableK8Cluster: pulumi.Bool(true),
			AddressPrefix:   pulumi.String("10.22.0.0/16"),
		})
		if err != nil {
			return err
		}
		ctx.Export("infraName", infra.InfraName)
		ctx.Export("vpcId", infra.VpcId)

		// Create DuploCloud Tenant
		tenant, err := duplocloud.NewTenant(ctx, "dev", &duplocloud.TenantArgs{
			AccountName:   pulumi.String("dev"),
			PlanId:        infra.InfraName,
			AllowDeletion: pulumi.Bool(true),
		}, pulumi.DependsOn([]pulumi.Resource{infra}))
		if err != nil {
			return err
		}
		ctx.Export("tenantId", tenant.ID())

		// Get native image
		image := duplocloud.GetNativeHostImageOutput(ctx, duplocloud.GetNativeHostImageOutputArgs{
			TenantId:     tenant.TenantId,
			IsKubernetes: pulumi.Bool(true),
		}, nil)

		// Create EKS Node
		node, err := duplocloud.NewAwsHost(ctx, "node", &duplocloud.AwsHostArgs{
			TenantId:      tenant.TenantId,
			FriendlyName:  pulumi.String("node01"),
			ImageId:       image.ImageId(),
			Capacity:      pulumi.String("t3a.medium"),
			AgentPlatform: pulumi.Int(7),
			Zone:          pulumi.Int(0),
			Metadatas: duplocloud.AwsHostMetadataArray{
				&duplocloud.AwsHostMetadataArgs{
					Key:   pulumi.String("OsDiskSize"),
					Value: pulumi.String("20"),
				},
			},
		}, pulumi.DependsOn([]pulumi.Resource{tenant, infra}))
		if err != nil {
			return err
		}

		// Create a service
		webapp, err := duplocloud.NewDuploService(ctx, "web-app", &duplocloud.DuploServiceArgs{
			TenantId:      tenant.TenantId,
			Name:          pulumi.String("web-app"),
			AgentPlatform: pulumi.Int(7),
			DockerImage:   pulumi.String("nginx:latest"),
			Replicas:      pulumi.Int(1),
		}, pulumi.DependsOn([]pulumi.Resource{node, tenant, infra}))
		if err != nil {
			return err
		}

		// Configure Load Balancer
		cert_arn := "arn:aws:acm:us-east-1:1234567890:certificate/d6c4138f-583e-4c75-a314-851142670b64"
		_, err = duplocloud.NewDuploServiceLbconfigs(ctx, "web-app-lb", &duplocloud.DuploServiceLbconfigsArgs{
			TenantId:                  webapp.TenantId,
			ReplicationControllerName: webapp.Name,
			Lbconfigs: duplocloud.DuploServiceLbconfigsLbconfigArray{
				&duplocloud.DuploServiceLbconfigsLbconfigArgs{
					ExternalPort:   pulumi.Int(443),
					HealthCheckUrl: pulumi.String("/"),
					IsNative:       pulumi.Bool(false),
					LbType:         pulumi.Int(1),
					Port:           pulumi.String("80"),
					Protocol:       pulumi.String("http"),
					CertificateArn: pulumi.String(cert_arn),
					HealthCheck: &duplocloud.DuploServiceLbconfigsLbconfigHealthCheckArgs{
						HealthyThreshold:   pulumi.Int(4),
						UnhealthyThreshold: pulumi.Int(4),
						Timeout:            pulumi.Int(50),
						Interval:           pulumi.Int(30),
						HttpSuccessCodes:   pulumi.String("200-399"),
					},
				},
			},
		}, pulumi.DependsOn([]pulumi.Resource{webapp, node, tenant, infra}))
		if err != nil {
			return err
		}
		return nil
	})
}
```

### Python

```python
import pulumi
import pulumi_duplocloud as duplo

# Create DuploCloud Infrastructure
infra = duplo.infrastructure.Infrastructure(resource_name="pulumi-infra",
    infra_name="pulumi-infra",
    cloud=0,
    region="us-east-2",
    azcount=2,
    subnet_cidr=24,
    address_prefix="10.22.0.0/16",
    enable_k8_cluster=True,  # Enable Kubernetes
)

# Export the outputs
pulumi.export("vpc_id", infra.vpc_id)

# Create Tenant
tenant = duplo.tenant.Tenant(resource_name="dev",
    account_name="dev",
    plan_id=infra.infra_name,
)

# Export the outputs
pulumi.export("tenantId", tenant.tenant_id)

# Create EKS Node
image = duplo.get_native_host_image_output(tenant_id=tenant.tenant_id,
            is_kubernetes=True)

node = duplo.AwsHost(resource_name="Node01",
    tenant_id=tenant.tenant_id,
    friendly_name="Node01",
    image_id=image.image_id,
    capacity="t3a.medium",
    agent_platform=7,
    zone=0,
    metadatas=[{
        "key": "OsDiskSize",
        "value": "20",
    }]
)

# Deploy nginx service on EKS

cert_arn="arn:aws:acm:us-east-1:1234567890:certificate/d6c4138f-583e-4c75-a314-851142670b64"
app_service = duplo.duplo_service.DuploService(resource_name="web-application",
    opts=pulumi.ResourceOptions(depends_on=[node]),
    tenant_id=tenant.tenant_id,
    name="web-app",
    docker_image="nginx:latest",
    replicas=1,
    agent_platform=7,
)

# Configure Load Balancer
app_lbconfigs = duplo.DuploServiceLbconfigs(resource_name="web-application-lb",
    tenant_id=tenant.tenant_id,
    replication_controller_name=app_service.name,
    lbconfigs=[{
        "external_port": 443,
        "health_check_url": "/",
        "is_native": False,
        "lb_type": 1,
        "port": "80",
        "protocol": "http",
        "certificate_arn":  cert_arn,
        "health_check": {
            "healthy_threshold": 4,
            "unhealthy_threshold": 4,
            "timeout": 10,
            "interval": 30,
            "http_success_codes": "200-399",
        },
    }]
)

```

### TypeScript

```typescript
import * as duplocloud from "@duplocloud/pulumi";

const certArn = "arn:aws:acm:us-east-1:1234567890:certificate/d6c4138f-583e-4c75-a314-851142670b64"

// Create DuploCloud infrastructure
const infra = new duplocloud.Infrastructure("infra", {
    infraName: "pulumi-infra",
    cloud: 0,
    region: "us-east-2",
    azcount: 2,
    subnetCidr: 24,
    enableK8Cluster: true,
    addressPrefix: "10.22.0.0/16",
});

export const vpcId = infra.vpcId;

// Create DuploCloud tenant
const tenant = new duplocloud.Tenant("dev", {
    accountName: "dev",
    planId: infra.infraName,
}, { dependsOn: [infra] });

export const tenantId = tenant.tenantId;

const image = duplocloud.getNativeHostImageOutput({
    tenantId: tenant.tenantId,
    isKubernetes: true,
});

// Create DuploCloud node
const node = new duplocloud.AwsHost("Node01", {
    tenantId: tenant.tenantId,
    friendlyName: "Node01",
    imageId: image.imageId,
    capacity: "t3a.medium",
    agentPlatform: 7,
    zone: 0,
    metadatas: [{
        key: "OsDiskSize",
        value: "20",
    }],
}, { dependsOn: [tenant] });

// Create DuploCloud service
const app_service = new duplocloud.DuploService("web-application", {
    tenantId: tenant.tenantId,
    name: "web-app",
    agentPlatform: 7,
    dockerImage: "nginx:latest",
    replicas: 1,
}, { dependsOn: [node] });

// Create DuploCloud load balancer
const appLbconfigs = new duplocloud.DuploServiceLbconfigs("web-application-lbconfigs", {
    tenantId: app_service.tenantId,
    replicationControllerName: app_service.name,
    lbconfigs: [{
        externalPort: 80,
        healthCheckUrl: "/",
        isNative: false,
        lbType: 1,
        port: "80",
        protocol: "http",
        certificateArn: certArn,
        healthCheck: {
            healthyThreshold: 4,
            unhealthyThreshold: 4,
            timeout: 50,
            interval: 30,
            httpSuccessCodes: "200-399",
        },
    }],
});
```

### C#

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Pulumi;
using Duplocloud = DuploCloud.Pulumi;

return await Deployment.RunAsync(() =>
{

    // Create a new infrastructure in AWS
    var infra = new Duplocloud.Infrastructure("pulumi-infra", new Duplocloud.InfrastructureArgs
    {
        InfraName = "pulumi-infra",
        Cloud = 0,
        Region = "us-east-2",
        Azcount = 2,
        EnableK8Cluster = true,
        AddressPrefix = "10.22.0.0/16",
        SubnetCidr = 24,
    });
    infra.VpcId.Apply(id =>
    {
        Pulumi.Log.Info($"VPC ID : {id}");
        return id;
    });

    // Create tenant
    var tenant = new Duplocloud.Tenant("dev", new()
    {
        AccountName = "dev",
        PlanId = infra.InfraName,
    },
    new CustomResourceOptions { DependsOn = { infra } });

    tenant.TenantId.Apply(id =>
    {
        Pulumi.Log.Info($"Tenant ID : {id}");
        return id;
    });

    var imageOutput = Duplocloud.GetNativeHostImage.Invoke(new()
    {
        TenantId = tenant.TenantId,
        IsKubernetes = true,
    });

     imageOutput.Apply(image =>
    {
        Pulumi.Log.Info($"AMI ID : {image.ImageId}");
        return image.ImageId;
    });

    // Create EKS Node
    var host = new Duplocloud.AwsHost("Node01", new()
    {
        TenantId = tenant.TenantId,
        FriendlyName = "Node01",
        ImageId = imageOutput.Apply(image => image.ImageId),
        Capacity = "t3a.small",
        AgentPlatform = 7,
        Zone = 0,
        Metadatas = new[]
        {
            new Duplocloud.Inputs.AwsHostMetadataArgs
            {
                Key = "OsDiskSize",
                Value = "20",
            },
        },
    },
    new CustomResourceOptions { DependsOn = { tenant } });

    // Create EKS Deployment
    var certArn="arn:aws:acm:us-east-1:1234567890:certificate/d6c4138f-583e-4c75-a314-851142670b64";
    var appService = new Duplocloud.DuploService("web-application", new()
    {
        TenantId = tenant.TenantId,
        Name = "web-application",
        AgentPlatform = 7,
        DockerImage = "nginx:latest",
        Replicas = 1,
    },
    new CustomResourceOptions { DependsOn = { host } });

    // Create EKS Service
    var appLBConfigs = new Duplocloud.DuploServiceLbconfigs("web-application-lb", new()
    {
        TenantId = appService.TenantId,
        ReplicationControllerName = appService.Name,
        Lbconfigs = new[]
        {
            new Duplocloud.Inputs.DuploServiceLbconfigsLbconfigArgs
            {
                ExternalPort = 443,
                HealthCheckUrl = "/",
                IsNative = false,
                LbType = 1,
                Port = "80",
                Protocol = "http",
                CertificateArn = certArn,
                HealthCheck = new Duplocloud.Inputs.DuploServiceLbconfigsLbconfigHealthCheckArgs
                {
                    HealthyThreshold = 4,
                    UnhealthyThreshold = 4,
                    Timeout = 10,
                    Interval = 30,
                    HttpSuccessCodes = "200-399",
                },
            },
        },
    },
    new CustomResourceOptions { DependsOn = { appService } });

    return new Dictionary<string, object>
    {
        { "VpcId",  infra.VpcId },
        { "tenantId",  tenant.TenantId },
    };
});
```

## Development

### Building the Provider

To build the provider locally:

```bash
make build
```

This will:
- Build the provider binary
- Generate and build all language SDKs (Go, Python, Node.js, .NET)
- Install the provider and SDKs locally for testing

### Upgrading the Terraform Provider

This Pulumi provider is built on top of the [DuploCloud Terraform Provider](https://github.com/duplocloud/terraform-provider-duplocloud). To upgrade to a newer version of the Terraform provider:

#### Automated Upgrade (Recommended)

The repository includes automated workflows that check for new Terraform provider versions daily:

```bash
# Trigger upgrade workflow manually via GitHub CLI
gh workflow run upgrade-provider.yml -f version=0.11.31

# Or let it auto-detect the latest version
gh workflow run upgrade-provider.yml
```

You can also trigger it from the GitHub Actions UI at:
https://github.com/duplocloud/pulumi-duplocloud/actions/workflows/upgrade-provider.yml

#### Manual Upgrade

For manual upgrades, follow these steps:

```bash
# 1. Update the Terraform provider version in provider/go.mod
# Change: github.com/duplocloud/terraform-provider-duplocloud v0.11.0
# To:     github.com/duplocloud/terraform-provider-duplocloud v0.11.31

# 2. Update Go dependencies
cd provider && go mod tidy && cd ..

# 3. Regenerate the schema
make schema

# 4. Regenerate all language SDKs
make generate_sdks

# 5. Build and test
make build
make test_provider
```

For detailed instructions, see [UPGRADE_PROVIDER.md](./UPGRADE_PROVIDER.md).

### Running Tests

```bash
# Run provider tests
make test_provider

# Run example tests (requires DuploCloud credentials)
export duplo_host="https://your-instance.duplocloud.net"
export duplo_token="your-token"
make test
```

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.
