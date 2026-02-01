r'''
# @robhan-cdk-lib/aws_aps

AWS Cloud Development Kit (CDK) constructs for Amazon Managed Service for Prometheus.

In [aws-cdk-lib.aws_aps](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_aps-readme.html), there currently only exist L1 constructs for Amazon Managed Service for Prometheus.

While helpful, they miss convenience like:

* advanced parameter checking (min/max number values, string lengths, array lengths...) before CloudFormation deployment
* proper parameter typing, e.g. enum values instead of strings
* simply referencing other constructs instead of e.g. ARN strings

Those features are implemented here.

The CDK maintainers explain that [publishing your own package](https://github.com/aws/aws-cdk/blob/main/CONTRIBUTING.md#publishing-your-own-package) is "by far the strongest signal you can give to the CDK team that a feature should be included within the core aws-cdk packages".

This project aims to develop aws_aps constructs to a maturity that can potentially be accepted to the CDK core.

It is not supported by AWS and is not endorsed by them. Please file issues in the [GitHub repository](https://github.com/robert-hanuschke/cdk-aws_aps/issues) if you find any.

## Example use

```python
import * as cdk from 'aws-cdk-lib';
import { Subnet } from 'aws-cdk-lib/aws-ec2';
import { Cluster } from 'aws-cdk-lib/aws-eks';
import { Construct } from 'constructs';
import { Workspace, RuleGroupsNamespace, Scraper } from '@robhan-cdk-lib/aws_aps';

export class AwsApsCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const workspace = new Workspace(this, 'MyWorkspace', {});
    new RuleGroupsNamespace(this, 'MyRuleGroupsNamespace', { workspace, data: '<myRulesFileData>', name: 'myRuleGroupsNamespace' });
    new Scraper(this, 'MyScraper', {
      destination: {
        ampConfiguration: {
          workspace,
        },
      },
      source: {
        eksConfiguration: {
          cluster: Cluster.fromClusterAttributes(this, 'MyCluster', {
            clusterName: 'clusterName',
          }),
          subnets: [
            Subnet.fromSubnetAttributes(this, 'MySubnet', {
              subnetId: 'subnetId',
            }),
          ],
        },
      },
      scrapeConfiguration: {
        configurationBlob: '<myScrapeConfiguration>',
      },
    });
  }
}
```

## License

MIT
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_eks as _aws_cdk_aws_eks_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.AmpConfiguration",
    jsii_struct_bases=[],
    name_mapping={"workspace": "workspace"},
)
class AmpConfiguration:
    def __init__(self, *, workspace: "IWorkspace") -> None:
        '''The AmpConfiguration structure defines the Amazon Managed Service for Prometheus instance a scraper should send metrics to.

        :param workspace: The Amazon Managed Service for Prometheus workspace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b57f1ed441699407024d3a67f6d0ecf1fd33175a38d466e4e90e190923b70a0)
            check_type(argname="argument workspace", value=workspace, expected_type=type_hints["workspace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "workspace": workspace,
        }

    @builtins.property
    def workspace(self) -> "IWorkspace":
        '''The Amazon Managed Service for Prometheus workspace.'''
        result = self._values.get("workspace")
        assert result is not None, "Required property 'workspace' is missing"
        return typing.cast("IWorkspace", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AmpConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.AnomalyDetectorConfiguration",
    jsii_struct_bases=[],
    name_mapping={"random_cut_forest": "randomCutForest"},
)
class AnomalyDetectorConfiguration:
    def __init__(
        self,
        *,
        random_cut_forest: typing.Union["RandomCutForestConfiguration", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The configuration for the anomaly detection algorithm.

        :param random_cut_forest: The Random Cut Forest algorithm configuration for anomaly detection.
        '''
        if isinstance(random_cut_forest, dict):
            random_cut_forest = RandomCutForestConfiguration(**random_cut_forest)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__488e50421526d1e316a7bd2f186eccb1fc4bf1daba066e779c147e9e9dbc747a)
            check_type(argname="argument random_cut_forest", value=random_cut_forest, expected_type=type_hints["random_cut_forest"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "random_cut_forest": random_cut_forest,
        }

    @builtins.property
    def random_cut_forest(self) -> "RandomCutForestConfiguration":
        '''The Random Cut Forest algorithm configuration for anomaly detection.'''
        result = self._values.get("random_cut_forest")
        assert result is not None, "Required property 'random_cut_forest' is missing"
        return typing.cast("RandomCutForestConfiguration", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AnomalyDetectorConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.AnomalyDetectorProps",
    jsii_struct_bases=[],
    name_mapping={
        "alias": "alias",
        "configuration": "configuration",
        "workspace": "workspace",
        "evaluation_interval_in_seconds": "evaluationIntervalInSeconds",
        "labels": "labels",
        "missing_data_action": "missingDataAction",
    },
)
class AnomalyDetectorProps:
    def __init__(
        self,
        *,
        alias: builtins.str,
        configuration: typing.Union["AnomalyDetectorConfiguration", typing.Dict[builtins.str, typing.Any]],
        workspace: "IWorkspace",
        evaluation_interval_in_seconds: typing.Optional[jsii.Number] = None,
        labels: typing.Optional[typing.Sequence[typing.Union["Label", typing.Dict[builtins.str, typing.Any]]]] = None,
        missing_data_action: typing.Optional[typing.Union["MissingDataAction", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for creating an Amazon Managed Service for Prometheus Anomaly Detector.

        :param alias: The user-friendly name of the anomaly detector. 1 to 128 characters length.
        :param configuration: The algorithm configuration of the anomaly detector.
        :param workspace: An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.
        :param evaluation_interval_in_seconds: The frequency, in seconds, at which the anomaly detector evaluates metrics. Minimum value of 30. Maximum value of 86400.
        :param labels: The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector. Map Entries: Minimum number of 0 items. Maximum number of 140 items. Key Length Constraints: Minimum length of 1. Maximum length of 7168. Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]* Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        :param missing_data_action: The action taken when data is missing during evaluation.
        '''
        if isinstance(configuration, dict):
            configuration = AnomalyDetectorConfiguration(**configuration)
        if isinstance(missing_data_action, dict):
            missing_data_action = MissingDataAction(**missing_data_action)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d73bc4f90dcbc90f45d5d011fc423d2638eb9cfe65810e23594184c620ce38aa)
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument configuration", value=configuration, expected_type=type_hints["configuration"])
            check_type(argname="argument workspace", value=workspace, expected_type=type_hints["workspace"])
            check_type(argname="argument evaluation_interval_in_seconds", value=evaluation_interval_in_seconds, expected_type=type_hints["evaluation_interval_in_seconds"])
            check_type(argname="argument labels", value=labels, expected_type=type_hints["labels"])
            check_type(argname="argument missing_data_action", value=missing_data_action, expected_type=type_hints["missing_data_action"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "alias": alias,
            "configuration": configuration,
            "workspace": workspace,
        }
        if evaluation_interval_in_seconds is not None:
            self._values["evaluation_interval_in_seconds"] = evaluation_interval_in_seconds
        if labels is not None:
            self._values["labels"] = labels
        if missing_data_action is not None:
            self._values["missing_data_action"] = missing_data_action

    @builtins.property
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector.

        1 to 128 characters length.
        '''
        result = self._values.get("alias")
        assert result is not None, "Required property 'alias' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        result = self._values.get("configuration")
        assert result is not None, "Required property 'configuration' is missing"
        return typing.cast("AnomalyDetectorConfiguration", result)

    @builtins.property
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        result = self._values.get("workspace")
        assert result is not None, "Required property 'workspace' is missing"
        return typing.cast("IWorkspace", result)

    @builtins.property
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        result = self._values.get("evaluation_interval_in_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        result = self._values.get("labels")
        return typing.cast(typing.Optional[typing.List["Label"]], result)

    @builtins.property
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        result = self._values.get("missing_data_action")
        return typing.cast(typing.Optional["MissingDataAction"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AnomalyDetectorProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.CloudWatchLogDestination",
    jsii_struct_bases=[],
    name_mapping={"log_group": "logGroup"},
)
class CloudWatchLogDestination:
    def __init__(self, *, log_group: "_aws_cdk_aws_logs_ceddda9d.ILogGroup") -> None:
        '''Configuration details for logging to CloudWatch Logs.

        :param log_group: The CloudWatch log group.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f4c8d116f44cd0ce0c010e39612b1f9f3d190e82d3f5f4c0372ae03517a31a79)
            check_type(argname="argument log_group", value=log_group, expected_type=type_hints["log_group"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "log_group": log_group,
        }

    @builtins.property
    def log_group(self) -> "_aws_cdk_aws_logs_ceddda9d.ILogGroup":
        '''The CloudWatch log group.'''
        result = self._values.get("log_group")
        assert result is not None, "Required property 'log_group' is missing"
        return typing.cast("_aws_cdk_aws_logs_ceddda9d.ILogGroup", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CloudWatchLogDestination(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.Destination",
    jsii_struct_bases=[],
    name_mapping={"amp_configuration": "ampConfiguration"},
)
class Destination:
    def __init__(
        self,
        *,
        amp_configuration: typing.Union["AmpConfiguration", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''Where to send the metrics from a scraper.

        :param amp_configuration: The Amazon Managed Service for Prometheus workspace to send metrics to.
        '''
        if isinstance(amp_configuration, dict):
            amp_configuration = AmpConfiguration(**amp_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f247dc1883eff5c9525a2e09081bf65d9f34dc7f9581f5fcb643b104e14afa09)
            check_type(argname="argument amp_configuration", value=amp_configuration, expected_type=type_hints["amp_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "amp_configuration": amp_configuration,
        }

    @builtins.property
    def amp_configuration(self) -> "AmpConfiguration":
        '''The Amazon Managed Service for Prometheus workspace to send metrics to.'''
        result = self._values.get("amp_configuration")
        assert result is not None, "Required property 'amp_configuration' is missing"
        return typing.cast("AmpConfiguration", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Destination(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.EksConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "cluster": "cluster",
        "subnets": "subnets",
        "security_groups": "securityGroups",
    },
)
class EksConfiguration:
    def __init__(
        self,
        *,
        cluster: "_aws_cdk_aws_eks_ceddda9d.ICluster",
        subnets: typing.Sequence["_aws_cdk_aws_ec2_ceddda9d.ISubnet"],
        security_groups: typing.Optional[typing.Sequence["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]] = None,
    ) -> None:
        '''The EksConfiguration structure describes the connection to the Amazon EKS cluster from which a scraper collects metrics.

        :param cluster: The Amazon EKS cluster.
        :param subnets: A list of subnets for the Amazon EKS cluster VPC configuration. Min 1, max 5.
        :param security_groups: A list of the security group IDs for the Amazon EKS cluster VPC configuration. Min 1, max 5.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9e3526038ce65e3714e7b69cac8f1dac03b300f7ee7b6eb0a81f578bb9386261)
            check_type(argname="argument cluster", value=cluster, expected_type=type_hints["cluster"])
            check_type(argname="argument subnets", value=subnets, expected_type=type_hints["subnets"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cluster": cluster,
            "subnets": subnets,
        }
        if security_groups is not None:
            self._values["security_groups"] = security_groups

    @builtins.property
    def cluster(self) -> "_aws_cdk_aws_eks_ceddda9d.ICluster":
        '''The Amazon EKS cluster.'''
        result = self._values.get("cluster")
        assert result is not None, "Required property 'cluster' is missing"
        return typing.cast("_aws_cdk_aws_eks_ceddda9d.ICluster", result)

    @builtins.property
    def subnets(self) -> typing.List["_aws_cdk_aws_ec2_ceddda9d.ISubnet"]:
        '''A list of subnets for the Amazon EKS cluster VPC configuration.

        Min 1, max 5.
        '''
        result = self._values.get("subnets")
        assert result is not None, "Required property 'subnets' is missing"
        return typing.cast(typing.List["_aws_cdk_aws_ec2_ceddda9d.ISubnet"], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]]:
        '''A list of the security group IDs for the Amazon EKS cluster VPC configuration.

        Min 1, max 5.
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EksConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_aps.IAnomalyDetector")
class IAnomalyDetector(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector. 1 to 128 characters length.

        Minimum length of 1. Maximum length of 64.
        Pattern: [0-9A-Za-z][-.0-9A-Z_a-z]*
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectorArn")
    def anomaly_detector_arn(self) -> builtins.str:
        '''The Amazon Resource Name (ARN) of the anomaly detector.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="configuration")
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="evaluationIntervalInSeconds")
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="labels")
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="missingDataAction")
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        ...


class _IAnomalyDetectorProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_aps.IAnomalyDetector"

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector. 1 to 128 characters length.

        Minimum length of 1. Maximum length of 64.
        Pattern: [0-9A-Za-z][-.0-9A-Z_a-z]*
        '''
        return typing.cast(builtins.str, jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectorArn")
    def anomaly_detector_arn(self) -> builtins.str:
        '''The Amazon Resource Name (ARN) of the anomaly detector.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "anomalyDetectorArn"))

    @builtins.property
    @jsii.member(jsii_name="configuration")
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        return typing.cast("AnomalyDetectorConfiguration", jsii.get(self, "configuration"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

    @builtins.property
    @jsii.member(jsii_name="evaluationIntervalInSeconds")
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "evaluationIntervalInSeconds"))

    @builtins.property
    @jsii.member(jsii_name="labels")
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        return typing.cast(typing.Optional[typing.List["Label"]], jsii.get(self, "labels"))

    @builtins.property
    @jsii.member(jsii_name="missingDataAction")
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        return typing.cast(typing.Optional["MissingDataAction"], jsii.get(self, "missingDataAction"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IAnomalyDetector).__jsii_proxy_class__ = lambda : _IAnomalyDetectorProxy


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_aps.IResourcePolicy")
class IResourcePolicy(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="policyDocument")
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        ...


class _IResourcePolicyProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_aps.IResourcePolicy"

    @builtins.property
    @jsii.member(jsii_name="policyDocument")
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        return typing.cast(builtins.str, jsii.get(self, "policyDocument"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IResourcePolicy).__jsii_proxy_class__ = lambda : _IResourcePolicyProxy


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_aps.IRuleGroupsNamespace")
class IRuleGroupsNamespace(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="data")
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="ruleGroupsNamespaceArn")
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The ARN of the rule groups namespace.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        ...


class _IRuleGroupsNamespaceProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_aps.IRuleGroupsNamespace"

    @builtins.property
    @jsii.member(jsii_name="data")
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "data"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="ruleGroupsNamespaceArn")
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The ARN of the rule groups namespace.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "ruleGroupsNamespaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IRuleGroupsNamespace).__jsii_proxy_class__ = lambda : _IRuleGroupsNamespaceProxy


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_aps.IScraper")
class IScraper(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="destination")
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="scrapeConfiguration")
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="scraperArn")
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="scraperId")
    def scraper_id(self) -> builtins.str:
        '''The ID of the scraper.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="roleConfiguration")
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        ...


class _IScraperProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_aps.IScraper"

    @builtins.property
    @jsii.member(jsii_name="destination")
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        return typing.cast("Destination", jsii.get(self, "destination"))

    @builtins.property
    @jsii.member(jsii_name="scrapeConfiguration")
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        return typing.cast("ScrapeConfiguration", jsii.get(self, "scrapeConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="scraperArn")
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "scraperArn"))

    @builtins.property
    @jsii.member(jsii_name="scraperId")
    def scraper_id(self) -> builtins.str:
        '''The ID of the scraper.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "scraperId"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        return typing.cast("Source", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="roleConfiguration")
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        return typing.cast(typing.Optional["RoleConfiguration"], jsii.get(self, "roleConfiguration"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IScraper).__jsii_proxy_class__ = lambda : _IScraperProxy


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_aps.IWorkspace")
class IWorkspace(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="workspaceArn")
    def workspace_arn(self) -> builtins.str:
        '''The ARN of the workspace.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    def workspace_id(self) -> builtins.str:
        '''The unique ID for the workspace.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="alertManagerDefinition")
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="queryLoggingConfiguration")
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspaceConfiguration")
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        ...


class _IWorkspaceProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_aps.IWorkspace"

    @builtins.property
    @jsii.member(jsii_name="workspaceArn")
    def workspace_arn(self) -> builtins.str:
        '''The ARN of the workspace.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "workspaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    def workspace_id(self) -> builtins.str:
        '''The unique ID for the workspace.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "workspaceId"))

    @builtins.property
    @jsii.member(jsii_name="alertManagerDefinition")
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alertManagerDefinition"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="queryLoggingConfiguration")
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional["QueryLoggingConfiguration"], jsii.get(self, "queryLoggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="workspaceConfiguration")
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        return typing.cast(typing.Optional["WorkspaceConfiguration"], jsii.get(self, "workspaceConfiguration"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IWorkspace).__jsii_proxy_class__ = lambda : _IWorkspaceProxy


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.IgnoreNearExpected",
    jsii_struct_bases=[],
    name_mapping={"amount": "amount", "ratio": "ratio"},
)
class IgnoreNearExpected:
    def __init__(
        self,
        *,
        amount: typing.Optional[jsii.Number] = None,
        ratio: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Configuration for threshold settings that determine when values near expected values should be ignored during anomaly detection.

        :param amount: The absolute amount by which values can differ from expected values before being considered anomalous.
        :param ratio: The ratio by which values can differ from expected values before being considered anomalous.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa12ec68028f74d5d8f1d96a0b99090659c404c86bd0ec936014ab264467ca22)
            check_type(argname="argument amount", value=amount, expected_type=type_hints["amount"])
            check_type(argname="argument ratio", value=ratio, expected_type=type_hints["ratio"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if amount is not None:
            self._values["amount"] = amount
        if ratio is not None:
            self._values["ratio"] = ratio

    @builtins.property
    def amount(self) -> typing.Optional[jsii.Number]:
        '''The absolute amount by which values can differ from expected values before being considered anomalous.'''
        result = self._values.get("amount")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def ratio(self) -> typing.Optional[jsii.Number]:
        '''The ratio by which values can differ from expected values before being considered anomalous.'''
        result = self._values.get("ratio")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IgnoreNearExpected(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.Label",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class Label:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''A label is a name:value pair used to add context to ingested metrics.

        This structure defines the
        name and value for one label that is used in a label set. You can set ingestion limits on time
        series that match defined label sets, to help prevent a workspace from being overwhelmed with
        unexpected spikes in time series ingestion.

        :param name: The name for this label. Pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$ At least one character.
        :param value: The value for this label. At least one character.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c797aa51820ba19e3974b523e246d357e3b44ff0bc743b0f1171b5ae9bebdea)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''The name for this label.

        Pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$

        At least one character.
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''The value for this label.

        At least one character.
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Label(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.LimitsPerLabelSet",
    jsii_struct_bases=[],
    name_mapping={"label_set": "labelSet", "limits": "limits"},
)
class LimitsPerLabelSet:
    def __init__(
        self,
        *,
        label_set: typing.Sequence[typing.Union["Label", typing.Dict[builtins.str, typing.Any]]],
        limits: typing.Union["LimitsPerLabelSetEntry", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''This defines a label set for the workspace, and defines the ingestion limit for active time series that match that label set.

        Each label name in a label set must be unique.

        :param label_set: This defines one label set that will have an enforced ingestion limit. You can set ingestion limits on time series that match defined label sets, to help prevent a workspace from being overwhelmed with unexpected spikes in time series ingestion. Label values accept all UTF-8 characters with one exception. If the label name is metric name label **name**, then the metric part of the name must conform to the following pattern: [a-zA-Z_:][a-zA-Z0-9_:]* Minimum 0
        :param limits: This structure contains the information about the limits that apply to time series that match this label set.
        '''
        if isinstance(limits, dict):
            limits = LimitsPerLabelSetEntry(**limits)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6893b1308b220935b9f1ce7c4eae4ddc73c29be6663d247911732ccfcec7f4d9)
            check_type(argname="argument label_set", value=label_set, expected_type=type_hints["label_set"])
            check_type(argname="argument limits", value=limits, expected_type=type_hints["limits"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "label_set": label_set,
            "limits": limits,
        }

    @builtins.property
    def label_set(self) -> typing.List["Label"]:
        '''This defines one label set that will have an enforced ingestion limit.

        You can set ingestion
        limits on time series that match defined label sets, to help prevent a workspace from being
        overwhelmed with unexpected spikes in time series ingestion.

        Label values accept all UTF-8 characters with one exception. If the label name is metric
        name label **name**, then the metric part of the name must conform to the following pattern:
        [a-zA-Z_:][a-zA-Z0-9_:]*

        Minimum 0
        '''
        result = self._values.get("label_set")
        assert result is not None, "Required property 'label_set' is missing"
        return typing.cast(typing.List["Label"], result)

    @builtins.property
    def limits(self) -> "LimitsPerLabelSetEntry":
        '''This structure contains the information about the limits that apply to time series that match this label set.'''
        result = self._values.get("limits")
        assert result is not None, "Required property 'limits' is missing"
        return typing.cast("LimitsPerLabelSetEntry", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LimitsPerLabelSet(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.LimitsPerLabelSetEntry",
    jsii_struct_bases=[],
    name_mapping={"max_series": "maxSeries"},
)
class LimitsPerLabelSetEntry:
    def __init__(self, *, max_series: typing.Optional[jsii.Number] = None) -> None:
        '''This structure contains the limits that apply to time series that match one label set.

        :param max_series: The maximum number of active series that can be ingested that match this label set. Setting this to 0 causes no label set limit to be enforced, but it does cause Amazon Managed Service for Prometheus to vend label set metrics to CloudWatch Logs. Minimum 0
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f53acc1bbc1fb66aa75ed0ff80395c4fd66be1563ee572788afab4e42af12da4)
            check_type(argname="argument max_series", value=max_series, expected_type=type_hints["max_series"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if max_series is not None:
            self._values["max_series"] = max_series

    @builtins.property
    def max_series(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of active series that can be ingested that match this label set.

        Setting this to 0 causes no label set limit to be enforced, but it does cause Amazon Managed
        Service for Prometheus to vend label set metrics to CloudWatch Logs.

        Minimum 0
        '''
        result = self._values.get("max_series")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LimitsPerLabelSetEntry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.LoggingConfiguration",
    jsii_struct_bases=[],
    name_mapping={"log_group": "logGroup"},
)
class LoggingConfiguration:
    def __init__(
        self,
        *,
        log_group: typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"] = None,
    ) -> None:
        '''Contains information about the rules and alerting logging configuration for the workspace.

        :param log_group: The CloudWatch log group to which the vended log data will be published.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__282c7cd599e82904024934838ca325999d8149f211c5885145973734c9c85b76)
            check_type(argname="argument log_group", value=log_group, expected_type=type_hints["log_group"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if log_group is not None:
            self._values["log_group"] = log_group

    @builtins.property
    def log_group(self) -> typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"]:
        '''The CloudWatch log group to which the vended log data will be published.'''
        result = self._values.get("log_group")
        return typing.cast(typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LoggingConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.LoggingDestination",
    jsii_struct_bases=[],
    name_mapping={"cloud_watch_logs": "cloudWatchLogs", "filters": "filters"},
)
class LoggingDestination:
    def __init__(
        self,
        *,
        cloud_watch_logs: typing.Union["CloudWatchLogDestination", typing.Dict[builtins.str, typing.Any]],
        filters: typing.Union["LoggingFilter", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The logging destination in an Amazon Managed Service for Prometheus workspace.

        :param cloud_watch_logs: Configuration details for logging to CloudWatch Logs.
        :param filters: Filtering criteria that determine which queries are logged.
        '''
        if isinstance(cloud_watch_logs, dict):
            cloud_watch_logs = CloudWatchLogDestination(**cloud_watch_logs)
        if isinstance(filters, dict):
            filters = LoggingFilter(**filters)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2496000b19af109fb0c5c290e32ab9bbc75be51fbfa27d16758c01f8baf00891)
            check_type(argname="argument cloud_watch_logs", value=cloud_watch_logs, expected_type=type_hints["cloud_watch_logs"])
            check_type(argname="argument filters", value=filters, expected_type=type_hints["filters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cloud_watch_logs": cloud_watch_logs,
            "filters": filters,
        }

    @builtins.property
    def cloud_watch_logs(self) -> "CloudWatchLogDestination":
        '''Configuration details for logging to CloudWatch Logs.'''
        result = self._values.get("cloud_watch_logs")
        assert result is not None, "Required property 'cloud_watch_logs' is missing"
        return typing.cast("CloudWatchLogDestination", result)

    @builtins.property
    def filters(self) -> "LoggingFilter":
        '''Filtering criteria that determine which queries are logged.'''
        result = self._values.get("filters")
        assert result is not None, "Required property 'filters' is missing"
        return typing.cast("LoggingFilter", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LoggingDestination(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.LoggingFilter",
    jsii_struct_bases=[],
    name_mapping={"qsp_threshold": "qspThreshold"},
)
class LoggingFilter:
    def __init__(self, *, qsp_threshold: jsii.Number) -> None:
        '''Filtering criteria that determine which queries are logged.

        :param qsp_threshold: Integer. Minimum 0
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7beea1121128e5f35f0720b90b21713abba4beef8755e891bbf87c2ad9711a0)
            check_type(argname="argument qsp_threshold", value=qsp_threshold, expected_type=type_hints["qsp_threshold"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "qsp_threshold": qsp_threshold,
        }

    @builtins.property
    def qsp_threshold(self) -> jsii.Number:
        '''Integer.

        Minimum 0
        '''
        result = self._values.get("qsp_threshold")
        assert result is not None, "Required property 'qsp_threshold' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LoggingFilter(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.MissingDataAction",
    jsii_struct_bases=[],
    name_mapping={"mark_as_anomaly": "markAsAnomaly", "skip": "skip"},
)
class MissingDataAction:
    def __init__(
        self,
        *,
        mark_as_anomaly: typing.Optional[builtins.bool] = None,
        skip: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Specifies the action to take when data is missing during anomaly detection evaluation.

        :param mark_as_anomaly: Marks missing data points as anomalies.
        :param skip: Skips evaluation when data is missing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4de31fdb80b9646037b68b88ae1dae6b46be704ab84a3c61100b29e91fc959c2)
            check_type(argname="argument mark_as_anomaly", value=mark_as_anomaly, expected_type=type_hints["mark_as_anomaly"])
            check_type(argname="argument skip", value=skip, expected_type=type_hints["skip"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if mark_as_anomaly is not None:
            self._values["mark_as_anomaly"] = mark_as_anomaly
        if skip is not None:
            self._values["skip"] = skip

    @builtins.property
    def mark_as_anomaly(self) -> typing.Optional[builtins.bool]:
        '''Marks missing data points as anomalies.'''
        result = self._values.get("mark_as_anomaly")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip(self) -> typing.Optional[builtins.bool]:
        '''Skips evaluation when data is missing.'''
        result = self._values.get("skip")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MissingDataAction(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.QueryLoggingConfiguration",
    jsii_struct_bases=[],
    name_mapping={"destinations": "destinations"},
)
class QueryLoggingConfiguration:
    def __init__(
        self,
        *,
        destinations: typing.Sequence[typing.Union["LoggingDestination", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''The query logging configuration in an Amazon Managed Service for Prometheus workspace.

        :param destinations: Defines a destination and its associated filtering criteria for query logging. Minimum 1 and maximum 1 item in array.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__092820c29e1435155b193e5488fd2841dcea5141110ab984fa14a237e2f4a4ae)
            check_type(argname="argument destinations", value=destinations, expected_type=type_hints["destinations"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "destinations": destinations,
        }

    @builtins.property
    def destinations(self) -> typing.List["LoggingDestination"]:
        '''Defines a destination and its associated filtering criteria for query logging.

        Minimum 1 and maximum 1 item in array.
        '''
        result = self._values.get("destinations")
        assert result is not None, "Required property 'destinations' is missing"
        return typing.cast(typing.List["LoggingDestination"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "QueryLoggingConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.RandomCutForestConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "query": "query",
        "ignore_near_expected_from_above": "ignoreNearExpectedFromAbove",
        "ignore_near_expected_from_below": "ignoreNearExpectedFromBelow",
        "sample_size": "sampleSize",
        "shingle_size": "shingleSize",
    },
)
class RandomCutForestConfiguration:
    def __init__(
        self,
        *,
        query: builtins.str,
        ignore_near_expected_from_above: typing.Optional[typing.Union["IgnoreNearExpected", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_near_expected_from_below: typing.Optional[typing.Union["IgnoreNearExpected", typing.Dict[builtins.str, typing.Any]]] = None,
        sample_size: typing.Optional[jsii.Number] = None,
        shingle_size: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Configuration for the Random Cut Forest algorithm used for anomaly detection in time-series data.

        :param query: The Prometheus query used to retrieve the time-series data for anomaly detection. 1 to 8192 characters length.
        :param ignore_near_expected_from_above: Configuration for ignoring values that are near expected values from above during anomaly detection.
        :param ignore_near_expected_from_below: Configuration for ignoring values that are near expected values from below during anomaly detection.
        :param sample_size: The number of data points sampled from the input stream for the Random Cut Forest algorithm. The default number is 256 consecutive data points. Minimum: 256 Maximum: 1024
        :param shingle_size: The number of consecutive data points used to create a shingle for the Random Cut Forest algorithm. The default number is 8 consecutive data points. Minimum: 2 Maximum: 1024
        '''
        if isinstance(ignore_near_expected_from_above, dict):
            ignore_near_expected_from_above = IgnoreNearExpected(**ignore_near_expected_from_above)
        if isinstance(ignore_near_expected_from_below, dict):
            ignore_near_expected_from_below = IgnoreNearExpected(**ignore_near_expected_from_below)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c44dedd708a153df90c20f2738e66c34f510bb7ed036637ccb7a1bde1f3394b8)
            check_type(argname="argument query", value=query, expected_type=type_hints["query"])
            check_type(argname="argument ignore_near_expected_from_above", value=ignore_near_expected_from_above, expected_type=type_hints["ignore_near_expected_from_above"])
            check_type(argname="argument ignore_near_expected_from_below", value=ignore_near_expected_from_below, expected_type=type_hints["ignore_near_expected_from_below"])
            check_type(argname="argument sample_size", value=sample_size, expected_type=type_hints["sample_size"])
            check_type(argname="argument shingle_size", value=shingle_size, expected_type=type_hints["shingle_size"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "query": query,
        }
        if ignore_near_expected_from_above is not None:
            self._values["ignore_near_expected_from_above"] = ignore_near_expected_from_above
        if ignore_near_expected_from_below is not None:
            self._values["ignore_near_expected_from_below"] = ignore_near_expected_from_below
        if sample_size is not None:
            self._values["sample_size"] = sample_size
        if shingle_size is not None:
            self._values["shingle_size"] = shingle_size

    @builtins.property
    def query(self) -> builtins.str:
        '''The Prometheus query used to retrieve the time-series data for anomaly detection.

        1 to 8192 characters length.
        '''
        result = self._values.get("query")
        assert result is not None, "Required property 'query' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ignore_near_expected_from_above(self) -> typing.Optional["IgnoreNearExpected"]:
        '''Configuration for ignoring values that are near expected values from above during anomaly detection.'''
        result = self._values.get("ignore_near_expected_from_above")
        return typing.cast(typing.Optional["IgnoreNearExpected"], result)

    @builtins.property
    def ignore_near_expected_from_below(self) -> typing.Optional["IgnoreNearExpected"]:
        '''Configuration for ignoring values that are near expected values from below during anomaly detection.'''
        result = self._values.get("ignore_near_expected_from_below")
        return typing.cast(typing.Optional["IgnoreNearExpected"], result)

    @builtins.property
    def sample_size(self) -> typing.Optional[jsii.Number]:
        '''The number of data points sampled from the input stream for the Random Cut Forest algorithm.

        The default number is 256 consecutive data points.

        Minimum: 256
        Maximum: 1024
        '''
        result = self._values.get("sample_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def shingle_size(self) -> typing.Optional[jsii.Number]:
        '''The number of consecutive data points used to create a shingle for the Random Cut Forest algorithm.

        The default number is 8 consecutive data points.

        Minimum: 2
        Maximum: 1024
        '''
        result = self._values.get("shingle_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RandomCutForestConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IResourcePolicy)
class ResourcePolicyBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_aps.ResourcePolicyBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1705a6716ddb826f74670d4b351789ae363cbbc6a4fda6389f3fe972e4ad37e8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="policyDocument")
    @abc.abstractmethod
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    @abc.abstractmethod
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        ...


class _ResourcePolicyBaseProxy(
    ResourcePolicyBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="policyDocument")
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        return typing.cast(builtins.str, jsii.get(self, "policyDocument"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ResourcePolicyBase).__jsii_proxy_class__ = lambda : _ResourcePolicyBaseProxy


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.ResourcePolicyProps",
    jsii_struct_bases=[],
    name_mapping={"policy_document": "policyDocument", "workspace": "workspace"},
)
class ResourcePolicyProps:
    def __init__(
        self,
        *,
        policy_document: builtins.str,
        workspace: "IWorkspace",
    ) -> None:
        '''Properties for creating an Amazon Managed Service for Prometheus Resource Policy.

        :param policy_document: The JSON to use as the Resource-based Policy.
        :param workspace: The workspace to attach the policy to.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e64bdaac8096e1f570bf3bdd34320a336689a41b7fadad148bbe26533f682a36)
            check_type(argname="argument policy_document", value=policy_document, expected_type=type_hints["policy_document"])
            check_type(argname="argument workspace", value=workspace, expected_type=type_hints["workspace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "policy_document": policy_document,
            "workspace": workspace,
        }

    @builtins.property
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        result = self._values.get("policy_document")
        assert result is not None, "Required property 'policy_document' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        result = self._values.get("workspace")
        assert result is not None, "Required property 'workspace' is missing"
        return typing.cast("IWorkspace", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourcePolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.RoleConfiguration",
    jsii_struct_bases=[],
    name_mapping={"source_role": "sourceRole", "target_role": "targetRole"},
)
class RoleConfiguration:
    def __init__(
        self,
        *,
        source_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
        target_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
    ) -> None:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.

        :param source_role: The source role.
        :param target_role: The target role.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e96c135bdcece9823caf073421082af151c59b6d52a5918bb38689bbca7ab2a3)
            check_type(argname="argument source_role", value=source_role, expected_type=type_hints["source_role"])
            check_type(argname="argument target_role", value=target_role, expected_type=type_hints["target_role"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if source_role is not None:
            self._values["source_role"] = source_role
        if target_role is not None:
            self._values["target_role"] = target_role

    @builtins.property
    def source_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The source role.'''
        result = self._values.get("source_role")
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], result)

    @builtins.property
    def target_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The target role.'''
        result = self._values.get("target_role")
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.RuleGroupsNamespaceAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "data": "data",
        "name": "name",
        "rule_groups_namespace_arn": "ruleGroupsNamespaceArn",
        "workspace": "workspace",
    },
)
class RuleGroupsNamespaceAttributes:
    def __init__(
        self,
        *,
        data: builtins.str,
        name: builtins.str,
        rule_groups_namespace_arn: builtins.str,
        workspace: "IWorkspace",
    ) -> None:
        '''Properties for importing a rule groups namespace in an Amazon Managed Service for Prometheus workspace from attributes.

        :param data: The rules file used in the namespace.
        :param name: The name of the rule groups namespace. Between 1 and 64 characters.
        :param rule_groups_namespace_arn: The ARN of the rule groups namespace.
        :param workspace: The workspace to add the rule groups namespace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aca59ceb33a6b456771bcbba45d97752cb2f2f13917c19b7e97cd69b7f165a45)
            check_type(argname="argument data", value=data, expected_type=type_hints["data"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument rule_groups_namespace_arn", value=rule_groups_namespace_arn, expected_type=type_hints["rule_groups_namespace_arn"])
            check_type(argname="argument workspace", value=workspace, expected_type=type_hints["workspace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "data": data,
            "name": name,
            "rule_groups_namespace_arn": rule_groups_namespace_arn,
            "workspace": workspace,
        }

    @builtins.property
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        result = self._values.get("data")
        assert result is not None, "Required property 'data' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.

        Between 1 and 64 characters.
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The ARN of the rule groups namespace.'''
        result = self._values.get("rule_groups_namespace_arn")
        assert result is not None, "Required property 'rule_groups_namespace_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        result = self._values.get("workspace")
        assert result is not None, "Required property 'workspace' is missing"
        return typing.cast("IWorkspace", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuleGroupsNamespaceAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IRuleGroupsNamespace)
class RuleGroupsNamespaceBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_aps.RuleGroupsNamespaceBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54435341b8b1c3c7efe004b41ef5c6d515fe3983bc74fae1b1b26947b9d05f20)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="data")
    @abc.abstractmethod
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="name")
    @abc.abstractmethod
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="ruleGroupsNamespaceArn")
    @abc.abstractmethod
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The ARN of the rule groups namespace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    @abc.abstractmethod
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        ...


class _RuleGroupsNamespaceBaseProxy(
    RuleGroupsNamespaceBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="data")
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "data"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="ruleGroupsNamespaceArn")
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The ARN of the rule groups namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "ruleGroupsNamespaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, RuleGroupsNamespaceBase).__jsii_proxy_class__ = lambda : _RuleGroupsNamespaceBaseProxy


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.RuleGroupsNamespaceProps",
    jsii_struct_bases=[],
    name_mapping={"data": "data", "name": "name", "workspace": "workspace"},
)
class RuleGroupsNamespaceProps:
    def __init__(
        self,
        *,
        data: builtins.str,
        name: builtins.str,
        workspace: "IWorkspace",
    ) -> None:
        '''Properties for creating a rule groups namespace in an Amazon Managed Service for Prometheus workspace.

        :param data: The rules file used in the namespace.
        :param name: The name of the rule groups namespace. Between 1 and 64 characters.
        :param workspace: The workspace to add the rule groups namespace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38cadfd9b05a1407d50e98748f6488d0e79d3484e75c5786ea83b3235d73c3e1)
            check_type(argname="argument data", value=data, expected_type=type_hints["data"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument workspace", value=workspace, expected_type=type_hints["workspace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "data": data,
            "name": name,
            "workspace": workspace,
        }

    @builtins.property
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        result = self._values.get("data")
        assert result is not None, "Required property 'data' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.

        Between 1 and 64 characters.
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        result = self._values.get("workspace")
        assert result is not None, "Required property 'workspace' is missing"
        return typing.cast("IWorkspace", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuleGroupsNamespaceProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.ScrapeConfiguration",
    jsii_struct_bases=[],
    name_mapping={"configuration_blob": "configurationBlob"},
)
class ScrapeConfiguration:
    def __init__(self, *, configuration_blob: builtins.str) -> None:
        '''A scrape configuration for a scraper, base 64 encoded.

        :param configuration_blob: The base 64 encoded scrape configuration file.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6313d0a5d8e3eda66be90025eafb5520d36fb7fb11adbc40c4398cb56b0ce09d)
            check_type(argname="argument configuration_blob", value=configuration_blob, expected_type=type_hints["configuration_blob"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "configuration_blob": configuration_blob,
        }

    @builtins.property
    def configuration_blob(self) -> builtins.str:
        '''The base 64 encoded scrape configuration file.'''
        result = self._values.get("configuration_blob")
        assert result is not None, "Required property 'configuration_blob' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScrapeConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.ScraperAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "destination": "destination",
        "scrape_configuration": "scrapeConfiguration",
        "scraper_arn": "scraperArn",
        "source": "source",
        "alias": "alias",
        "role_configuration": "roleConfiguration",
    },
)
class ScraperAttributes:
    def __init__(
        self,
        *,
        destination: typing.Union["Destination", typing.Dict[builtins.str, typing.Any]],
        scrape_configuration: typing.Union["ScrapeConfiguration", typing.Dict[builtins.str, typing.Any]],
        scraper_arn: builtins.str,
        source: typing.Union["Source", typing.Dict[builtins.str, typing.Any]],
        alias: typing.Optional[builtins.str] = None,
        role_configuration: typing.Optional[typing.Union["RoleConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for importing an Amazon Managed Service for Prometheus Scraper from attributes.

        :param destination: The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.
        :param scrape_configuration: The configuration in use by the scraper.
        :param scraper_arn: The ARN of the scraper.
        :param source: The Amazon EKS cluster from which the scraper collects metrics.
        :param alias: An optional user-assigned scraper alias. 1-100 characters. Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        :param role_configuration: The role configuration in an Amazon Managed Service for Prometheus scraper.
        '''
        if isinstance(destination, dict):
            destination = Destination(**destination)
        if isinstance(scrape_configuration, dict):
            scrape_configuration = ScrapeConfiguration(**scrape_configuration)
        if isinstance(source, dict):
            source = Source(**source)
        if isinstance(role_configuration, dict):
            role_configuration = RoleConfiguration(**role_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2aab74937b2fefec81fb3f25317393581e00fbda88f9d176c61fd521a9189d81)
            check_type(argname="argument destination", value=destination, expected_type=type_hints["destination"])
            check_type(argname="argument scrape_configuration", value=scrape_configuration, expected_type=type_hints["scrape_configuration"])
            check_type(argname="argument scraper_arn", value=scraper_arn, expected_type=type_hints["scraper_arn"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument role_configuration", value=role_configuration, expected_type=type_hints["role_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "destination": destination,
            "scrape_configuration": scrape_configuration,
            "scraper_arn": scraper_arn,
            "source": source,
        }
        if alias is not None:
            self._values["alias"] = alias
        if role_configuration is not None:
            self._values["role_configuration"] = role_configuration

    @builtins.property
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        result = self._values.get("destination")
        assert result is not None, "Required property 'destination' is missing"
        return typing.cast("Destination", result)

    @builtins.property
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        result = self._values.get("scrape_configuration")
        assert result is not None, "Required property 'scrape_configuration' is missing"
        return typing.cast("ScrapeConfiguration", result)

    @builtins.property
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.'''
        result = self._values.get("scraper_arn")
        assert result is not None, "Required property 'scraper_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        result = self._values.get("source")
        assert result is not None, "Required property 'source' is missing"
        return typing.cast("Source", result)

    @builtins.property
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        result = self._values.get("alias")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        result = self._values.get("role_configuration")
        return typing.cast(typing.Optional["RoleConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScraperAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IScraper)
class ScraperBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_aps.ScraperBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__79f44dd804edbb4f2d30815f15d40d8f8c94bc90ec7657ced6d4b8716930412f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="getScraperId")
    def _get_scraper_id(self, scraper_arn: builtins.str) -> builtins.str:
        '''
        :param scraper_arn: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__720023f01199e16b0b50b3928b380b6c70d0c625eb677c6631c94d1822effb36)
            check_type(argname="argument scraper_arn", value=scraper_arn, expected_type=type_hints["scraper_arn"])
        return typing.cast(builtins.str, jsii.invoke(self, "getScraperId", [scraper_arn]))

    @builtins.property
    @jsii.member(jsii_name="destination")
    @abc.abstractmethod
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="scrapeConfiguration")
    @abc.abstractmethod
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="scraperArn")
    @abc.abstractmethod
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="scraperId")
    @abc.abstractmethod
    def scraper_id(self) -> builtins.str:
        '''The ID of the scraper.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="source")
    @abc.abstractmethod
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="alias")
    @abc.abstractmethod
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="roleConfiguration")
    @abc.abstractmethod
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        ...


class _ScraperBaseProxy(
    ScraperBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="destination")
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        return typing.cast("Destination", jsii.get(self, "destination"))

    @builtins.property
    @jsii.member(jsii_name="scrapeConfiguration")
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        return typing.cast("ScrapeConfiguration", jsii.get(self, "scrapeConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="scraperArn")
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.'''
        return typing.cast(builtins.str, jsii.get(self, "scraperArn"))

    @builtins.property
    @jsii.member(jsii_name="scraperId")
    def scraper_id(self) -> builtins.str:
        '''The ID of the scraper.'''
        return typing.cast(builtins.str, jsii.get(self, "scraperId"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        return typing.cast("Source", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="roleConfiguration")
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        return typing.cast(typing.Optional["RoleConfiguration"], jsii.get(self, "roleConfiguration"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ScraperBase).__jsii_proxy_class__ = lambda : _ScraperBaseProxy


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.ScraperProps",
    jsii_struct_bases=[],
    name_mapping={
        "destination": "destination",
        "scrape_configuration": "scrapeConfiguration",
        "source": "source",
        "alias": "alias",
        "role_configuration": "roleConfiguration",
    },
)
class ScraperProps:
    def __init__(
        self,
        *,
        destination: typing.Union["Destination", typing.Dict[builtins.str, typing.Any]],
        scrape_configuration: typing.Union["ScrapeConfiguration", typing.Dict[builtins.str, typing.Any]],
        source: typing.Union["Source", typing.Dict[builtins.str, typing.Any]],
        alias: typing.Optional[builtins.str] = None,
        role_configuration: typing.Optional[typing.Union["RoleConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for creating an Amazon Managed Service for Prometheus Scraper.

        :param destination: The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.
        :param scrape_configuration: The configuration in use by the scraper.
        :param source: The Amazon EKS cluster from which the scraper collects metrics.
        :param alias: An optional user-assigned scraper alias. 1-100 characters. Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        :param role_configuration: The role configuration in an Amazon Managed Service for Prometheus scraper.
        '''
        if isinstance(destination, dict):
            destination = Destination(**destination)
        if isinstance(scrape_configuration, dict):
            scrape_configuration = ScrapeConfiguration(**scrape_configuration)
        if isinstance(source, dict):
            source = Source(**source)
        if isinstance(role_configuration, dict):
            role_configuration = RoleConfiguration(**role_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e27ba8269266aa91c926829a5c485aaf203a6638ce54c2fced4fdf950ba2e944)
            check_type(argname="argument destination", value=destination, expected_type=type_hints["destination"])
            check_type(argname="argument scrape_configuration", value=scrape_configuration, expected_type=type_hints["scrape_configuration"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument role_configuration", value=role_configuration, expected_type=type_hints["role_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "destination": destination,
            "scrape_configuration": scrape_configuration,
            "source": source,
        }
        if alias is not None:
            self._values["alias"] = alias
        if role_configuration is not None:
            self._values["role_configuration"] = role_configuration

    @builtins.property
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        result = self._values.get("destination")
        assert result is not None, "Required property 'destination' is missing"
        return typing.cast("Destination", result)

    @builtins.property
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        result = self._values.get("scrape_configuration")
        assert result is not None, "Required property 'scrape_configuration' is missing"
        return typing.cast("ScrapeConfiguration", result)

    @builtins.property
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        result = self._values.get("source")
        assert result is not None, "Required property 'source' is missing"
        return typing.cast("Source", result)

    @builtins.property
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.

        1-100 characters.

        Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        '''
        result = self._values.get("alias")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        result = self._values.get("role_configuration")
        return typing.cast(typing.Optional["RoleConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScraperProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.Source",
    jsii_struct_bases=[],
    name_mapping={"eks_configuration": "eksConfiguration"},
)
class Source:
    def __init__(
        self,
        *,
        eks_configuration: typing.Union["EksConfiguration", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The source of collected metrics for a scraper.

        :param eks_configuration: The Amazon EKS cluster from which a scraper collects metrics.
        '''
        if isinstance(eks_configuration, dict):
            eks_configuration = EksConfiguration(**eks_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f45388bb39e3b47ec674e4da970163a87c5fb85665ad1fc10517bafda034ad5)
            check_type(argname="argument eks_configuration", value=eks_configuration, expected_type=type_hints["eks_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "eks_configuration": eks_configuration,
        }

    @builtins.property
    def eks_configuration(self) -> "EksConfiguration":
        '''The Amazon EKS cluster from which a scraper collects metrics.'''
        result = self._values.get("eks_configuration")
        assert result is not None, "Required property 'eks_configuration' is missing"
        return typing.cast("EksConfiguration", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Source(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.WorkspaceAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "workspace_arn": "workspaceArn",
        "alert_manager_definition": "alertManagerDefinition",
        "alias": "alias",
        "kms_key": "kmsKey",
        "logging_configuration": "loggingConfiguration",
        "query_logging_configuration": "queryLoggingConfiguration",
        "workspace_configuration": "workspaceConfiguration",
    },
)
class WorkspaceAttributes:
    def __init__(
        self,
        *,
        workspace_arn: builtins.str,
        alert_manager_definition: typing.Optional[builtins.str] = None,
        alias: typing.Optional[builtins.str] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        query_logging_configuration: typing.Optional[typing.Union["QueryLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        workspace_configuration: typing.Optional[typing.Union["WorkspaceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for importing an Amazon Managed Service for Prometheus Workspace from attributes.

        :param workspace_arn: The arn of this workspace.
        :param alert_manager_definition: The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.
        :param alias: The alias that is assigned to this workspace to help identify it. It does not need to be unique.
        :param kms_key: The customer managed AWS KMS key to use for encrypting data within your workspace.
        :param logging_configuration: Contains information about the current rules and alerting logging configuration for the workspace. Note: These logging configurations are only for rules and alerting logs.
        :param query_logging_configuration: The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.
        :param workspace_configuration: Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.
        '''
        if isinstance(logging_configuration, dict):
            logging_configuration = LoggingConfiguration(**logging_configuration)
        if isinstance(query_logging_configuration, dict):
            query_logging_configuration = QueryLoggingConfiguration(**query_logging_configuration)
        if isinstance(workspace_configuration, dict):
            workspace_configuration = WorkspaceConfiguration(**workspace_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bbfa4d3de7b456e3faeccf136f83095036d68c2058e82076f7a678eeac164e17)
            check_type(argname="argument workspace_arn", value=workspace_arn, expected_type=type_hints["workspace_arn"])
            check_type(argname="argument alert_manager_definition", value=alert_manager_definition, expected_type=type_hints["alert_manager_definition"])
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument logging_configuration", value=logging_configuration, expected_type=type_hints["logging_configuration"])
            check_type(argname="argument query_logging_configuration", value=query_logging_configuration, expected_type=type_hints["query_logging_configuration"])
            check_type(argname="argument workspace_configuration", value=workspace_configuration, expected_type=type_hints["workspace_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "workspace_arn": workspace_arn,
        }
        if alert_manager_definition is not None:
            self._values["alert_manager_definition"] = alert_manager_definition
        if alias is not None:
            self._values["alias"] = alias
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if logging_configuration is not None:
            self._values["logging_configuration"] = logging_configuration
        if query_logging_configuration is not None:
            self._values["query_logging_configuration"] = query_logging_configuration
        if workspace_configuration is not None:
            self._values["workspace_configuration"] = workspace_configuration

    @builtins.property
    def workspace_arn(self) -> builtins.str:
        '''The arn of this workspace.'''
        result = self._values.get("workspace_arn")
        assert result is not None, "Required property 'workspace_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        result = self._values.get("alert_manager_definition")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        result = self._values.get("alias")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], result)

    @builtins.property
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        result = self._values.get("logging_configuration")
        return typing.cast(typing.Optional["LoggingConfiguration"], result)

    @builtins.property
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        result = self._values.get("query_logging_configuration")
        return typing.cast(typing.Optional["QueryLoggingConfiguration"], result)

    @builtins.property
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        result = self._values.get("workspace_configuration")
        return typing.cast(typing.Optional["WorkspaceConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WorkspaceAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IWorkspace)
class WorkspaceBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_aps.WorkspaceBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26324cd5062f2f5ec83013af6d021bcb8f2e2c6d4df14147a97bf35d099c4a1b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="getWorkspaceId")
    def _get_workspace_id(self, workspace_arn: builtins.str) -> builtins.str:
        '''
        :param workspace_arn: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3ac750f120961e0958cd690a53ccc4e09d55d88803a7e53ed9bc1e70a3a9a78)
            check_type(argname="argument workspace_arn", value=workspace_arn, expected_type=type_hints["workspace_arn"])
        return typing.cast(builtins.str, jsii.invoke(self, "getWorkspaceId", [workspace_arn]))

    @builtins.property
    @jsii.member(jsii_name="workspaceArn")
    @abc.abstractmethod
    def workspace_arn(self) -> builtins.str:
        '''The ARN of the workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    @abc.abstractmethod
    def workspace_id(self) -> builtins.str:
        '''The unique ID for the workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="alertManagerDefinition")
    @abc.abstractmethod
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="alias")
    @abc.abstractmethod
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    @abc.abstractmethod
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    @abc.abstractmethod
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="queryLoggingConfiguration")
    @abc.abstractmethod
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspaceConfiguration")
    @abc.abstractmethod
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        ...


class _WorkspaceBaseProxy(
    WorkspaceBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="workspaceArn")
    def workspace_arn(self) -> builtins.str:
        '''The ARN of the workspace.'''
        return typing.cast(builtins.str, jsii.get(self, "workspaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    def workspace_id(self) -> builtins.str:
        '''The unique ID for the workspace.'''
        return typing.cast(builtins.str, jsii.get(self, "workspaceId"))

    @builtins.property
    @jsii.member(jsii_name="alertManagerDefinition")
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alertManagerDefinition"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="queryLoggingConfiguration")
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional["QueryLoggingConfiguration"], jsii.get(self, "queryLoggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="workspaceConfiguration")
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        return typing.cast(typing.Optional["WorkspaceConfiguration"], jsii.get(self, "workspaceConfiguration"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, WorkspaceBase).__jsii_proxy_class__ = lambda : _WorkspaceBaseProxy


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.WorkspaceConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "limits_per_label_sets": "limitsPerLabelSets",
        "retention_period_in_days": "retentionPeriodInDays",
    },
)
class WorkspaceConfiguration:
    def __init__(
        self,
        *,
        limits_per_label_sets: typing.Optional[typing.Sequence[typing.Union["LimitsPerLabelSet", typing.Dict[builtins.str, typing.Any]]]] = None,
        retention_period_in_days: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.

        :param limits_per_label_sets: This is an array of structures, where each structure defines a label set for the workspace, and defines the ingestion limit for active time series for each of those label sets. Each label name in a label set must be unique. Minimum 0
        :param retention_period_in_days: Specifies how many days that metrics will be retained in the workspace. Minimum 1
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae4d82a0bb8d7f12fbf4cbe9ccc1b9bdb2415b0517e902e2bdbf5e5546c092ce)
            check_type(argname="argument limits_per_label_sets", value=limits_per_label_sets, expected_type=type_hints["limits_per_label_sets"])
            check_type(argname="argument retention_period_in_days", value=retention_period_in_days, expected_type=type_hints["retention_period_in_days"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if limits_per_label_sets is not None:
            self._values["limits_per_label_sets"] = limits_per_label_sets
        if retention_period_in_days is not None:
            self._values["retention_period_in_days"] = retention_period_in_days

    @builtins.property
    def limits_per_label_sets(
        self,
    ) -> typing.Optional[typing.List["LimitsPerLabelSet"]]:
        '''This is an array of structures, where each structure defines a label set for the workspace, and defines the ingestion limit for active time series for each of those label sets.

        Each
        label name in a label set must be unique.

        Minimum 0
        '''
        result = self._values.get("limits_per_label_sets")
        return typing.cast(typing.Optional[typing.List["LimitsPerLabelSet"]], result)

    @builtins.property
    def retention_period_in_days(self) -> typing.Optional[jsii.Number]:
        '''Specifies how many days that metrics will be retained in the workspace.

        Minimum 1
        '''
        result = self._values.get("retention_period_in_days")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WorkspaceConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_aps.WorkspaceProps",
    jsii_struct_bases=[],
    name_mapping={
        "alert_manager_definition": "alertManagerDefinition",
        "alias": "alias",
        "kms_key": "kmsKey",
        "logging_configuration": "loggingConfiguration",
        "query_logging_configuration": "queryLoggingConfiguration",
        "workspace_configuration": "workspaceConfiguration",
    },
)
class WorkspaceProps:
    def __init__(
        self,
        *,
        alert_manager_definition: typing.Optional[builtins.str] = None,
        alias: typing.Optional[builtins.str] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        query_logging_configuration: typing.Optional[typing.Union["QueryLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        workspace_configuration: typing.Optional[typing.Union["WorkspaceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for creating an Amazon Managed Service for Prometheus Workspace.

        :param alert_manager_definition: The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.
        :param alias: The alias that is assigned to this workspace to help identify it. It does not need to be unique. 0 to 100 characters
        :param kms_key: The customer managed AWS KMS key to use for encrypting data within your workspace.
        :param logging_configuration: Contains information about the current rules and alerting logging configuration for the workspace. Note: These logging configurations are only for rules and alerting logs.
        :param query_logging_configuration: The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.
        :param workspace_configuration: Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.
        '''
        if isinstance(logging_configuration, dict):
            logging_configuration = LoggingConfiguration(**logging_configuration)
        if isinstance(query_logging_configuration, dict):
            query_logging_configuration = QueryLoggingConfiguration(**query_logging_configuration)
        if isinstance(workspace_configuration, dict):
            workspace_configuration = WorkspaceConfiguration(**workspace_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__204cf0cc18e2fd2c643a33020d11a1d61cbfe8a2abd5cd5bda6a222e017e12ef)
            check_type(argname="argument alert_manager_definition", value=alert_manager_definition, expected_type=type_hints["alert_manager_definition"])
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument logging_configuration", value=logging_configuration, expected_type=type_hints["logging_configuration"])
            check_type(argname="argument query_logging_configuration", value=query_logging_configuration, expected_type=type_hints["query_logging_configuration"])
            check_type(argname="argument workspace_configuration", value=workspace_configuration, expected_type=type_hints["workspace_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if alert_manager_definition is not None:
            self._values["alert_manager_definition"] = alert_manager_definition
        if alias is not None:
            self._values["alias"] = alias
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if logging_configuration is not None:
            self._values["logging_configuration"] = logging_configuration
        if query_logging_configuration is not None:
            self._values["query_logging_configuration"] = query_logging_configuration
        if workspace_configuration is not None:
            self._values["workspace_configuration"] = workspace_configuration

    @builtins.property
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        result = self._values.get("alert_manager_definition")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it. It does not need to be unique.

        0 to 100 characters
        '''
        result = self._values.get("alias")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], result)

    @builtins.property
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        result = self._values.get("logging_configuration")
        return typing.cast(typing.Optional["LoggingConfiguration"], result)

    @builtins.property
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        result = self._values.get("query_logging_configuration")
        return typing.cast(typing.Optional["QueryLoggingConfiguration"], result)

    @builtins.property
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        result = self._values.get("workspace_configuration")
        return typing.cast(typing.Optional["WorkspaceConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WorkspaceProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IAnomalyDetector)
class AnomalyDetectorBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_aps.AnomalyDetectorBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__763ce8aef513d695a9ea5e157a4299be537296b8475d4cac315b4f595f7d0536)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="alias")
    @abc.abstractmethod
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector. 1 to 64 characters length.

        Minimum length of 1. Maximum length of 64.
        Pattern: [0-9A-Za-z][-.0-9A-Z_a-z]*
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectorArn")
    @abc.abstractmethod
    def anomaly_detector_arn(self) -> builtins.str:
        '''The Amazon Resource Name (ARN) of the anomaly detector.

        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="configuration")
    @abc.abstractmethod
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="workspace")
    @abc.abstractmethod
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="evaluationIntervalInSeconds")
    @abc.abstractmethod
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="labels")
    @abc.abstractmethod
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="missingDataAction")
    @abc.abstractmethod
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        ...


class _AnomalyDetectorBaseProxy(
    AnomalyDetectorBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector. 1 to 64 characters length.

        Minimum length of 1. Maximum length of 64.
        Pattern: [0-9A-Za-z][-.0-9A-Z_a-z]*
        '''
        return typing.cast(builtins.str, jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectorArn")
    def anomaly_detector_arn(self) -> builtins.str:
        '''The Amazon Resource Name (ARN) of the anomaly detector.

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "anomalyDetectorArn"))

    @builtins.property
    @jsii.member(jsii_name="configuration")
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        return typing.cast("AnomalyDetectorConfiguration", jsii.get(self, "configuration"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

    @builtins.property
    @jsii.member(jsii_name="evaluationIntervalInSeconds")
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "evaluationIntervalInSeconds"))

    @builtins.property
    @jsii.member(jsii_name="labels")
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        return typing.cast(typing.Optional[typing.List["Label"]], jsii.get(self, "labels"))

    @builtins.property
    @jsii.member(jsii_name="missingDataAction")
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        return typing.cast(typing.Optional["MissingDataAction"], jsii.get(self, "missingDataAction"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, AnomalyDetectorBase).__jsii_proxy_class__ = lambda : _AnomalyDetectorBaseProxy


class ResourcePolicy(
    ResourcePolicyBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_aps.ResourcePolicy",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        policy_document: builtins.str,
        workspace: "IWorkspace",
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param policy_document: The JSON to use as the Resource-based Policy.
        :param workspace: The workspace to attach the policy to.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__152018d2f86ee27c3ac817bf409dc2fae4034315290b87fd5d6c906625b633d3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ResourcePolicyProps(
            policy_document=policy_document, workspace=workspace
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="isResourcePolicy")
    @builtins.classmethod
    def is_resource_policy(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b7b7c7ca19cd491541f3243572cf47da8425bab13c98330c2653c2302cfa6b53)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isResourcePolicy", [x]))

    @builtins.property
    @jsii.member(jsii_name="policyDocument")
    def policy_document(self) -> builtins.str:
        '''The JSON to use as the Resource-based Policy.'''
        return typing.cast(builtins.str, jsii.get(self, "policyDocument"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to attach the policy to.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))


class RuleGroupsNamespace(
    RuleGroupsNamespaceBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_aps.RuleGroupsNamespace",
):
    '''The definition of a rule groups namespace in an Amazon Managed Service for Prometheus workspace.

    A rule groups namespace is associated with exactly one rules file. A workspace can have multiple
    rule groups namespaces.
    '''

    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        data: builtins.str,
        name: builtins.str,
        workspace: "IWorkspace",
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param data: The rules file used in the namespace.
        :param name: The name of the rule groups namespace. Between 1 and 64 characters.
        :param workspace: The workspace to add the rule groups namespace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d20ad42e4be3f2ea717b0a2a018087c9c8a4437ea677e47f420ba1b0b9d445d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RuleGroupsNamespaceProps(data=data, name=name, workspace=workspace)

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromRuleGroupsNamespaceAttributes")
    @builtins.classmethod
    def from_rule_groups_namespace_attributes(
        cls,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        data: builtins.str,
        name: builtins.str,
        rule_groups_namespace_arn: builtins.str,
        workspace: "IWorkspace",
    ) -> "IRuleGroupsNamespace":
        '''
        :param scope: -
        :param id: -
        :param data: The rules file used in the namespace.
        :param name: The name of the rule groups namespace. Between 1 and 64 characters.
        :param rule_groups_namespace_arn: The ARN of the rule groups namespace.
        :param workspace: The workspace to add the rule groups namespace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07bf6a97084316812dac20b3c71ddb45a75f79b4a8ec626bd6762069ada7d925)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = RuleGroupsNamespaceAttributes(
            data=data,
            name=name,
            rule_groups_namespace_arn=rule_groups_namespace_arn,
            workspace=workspace,
        )

        return typing.cast("IRuleGroupsNamespace", jsii.sinvoke(cls, "fromRuleGroupsNamespaceAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="isRuleGroupsNamespace")
    @builtins.classmethod
    def is_rule_groups_namespace(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9f121730976c1abb9dd8b8aeb3d4783892a3f693e887909348c16a32681593f4)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isRuleGroupsNamespace", [x]))

    @builtins.property
    @jsii.member(jsii_name="data")
    def data(self) -> builtins.str:
        '''The rules file used in the namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "data"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of the rule groups namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="ruleGroupsNamespaceArn")
    def rule_groups_namespace_arn(self) -> builtins.str:
        '''The workspace to add the rule groups namespace.'''
        return typing.cast(builtins.str, jsii.get(self, "ruleGroupsNamespaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''The workspace to add the rule groups namespace.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))


class Scraper(
    ScraperBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_aps.Scraper",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        destination: typing.Union["Destination", typing.Dict[builtins.str, typing.Any]],
        scrape_configuration: typing.Union["ScrapeConfiguration", typing.Dict[builtins.str, typing.Any]],
        source: typing.Union["Source", typing.Dict[builtins.str, typing.Any]],
        alias: typing.Optional[builtins.str] = None,
        role_configuration: typing.Optional[typing.Union["RoleConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param destination: The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.
        :param scrape_configuration: The configuration in use by the scraper.
        :param source: The Amazon EKS cluster from which the scraper collects metrics.
        :param alias: An optional user-assigned scraper alias. 1-100 characters. Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        :param role_configuration: The role configuration in an Amazon Managed Service for Prometheus scraper.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__420a8a3c500b6acbf7b84e9b716db0e0256ad4fe2f714daf764abfebb254c38a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ScraperProps(
            destination=destination,
            scrape_configuration=scrape_configuration,
            source=source,
            alias=alias,
            role_configuration=role_configuration,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromScraperAttributes")
    @builtins.classmethod
    def from_scraper_attributes(
        cls,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        destination: typing.Union["Destination", typing.Dict[builtins.str, typing.Any]],
        scrape_configuration: typing.Union["ScrapeConfiguration", typing.Dict[builtins.str, typing.Any]],
        scraper_arn: builtins.str,
        source: typing.Union["Source", typing.Dict[builtins.str, typing.Any]],
        alias: typing.Optional[builtins.str] = None,
        role_configuration: typing.Optional[typing.Union["RoleConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> "IScraper":
        '''
        :param scope: -
        :param id: -
        :param destination: The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.
        :param scrape_configuration: The configuration in use by the scraper.
        :param scraper_arn: The ARN of the scraper.
        :param source: The Amazon EKS cluster from which the scraper collects metrics.
        :param alias: An optional user-assigned scraper alias. 1-100 characters. Pattern: ^[0-9A-Za-z][-.0-9A-Z_a-z]*$
        :param role_configuration: The role configuration in an Amazon Managed Service for Prometheus scraper.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a782eecfe3a632aac5c0103f9029c7ec8a0b5f2ac8b500e9a0257a762eda243d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = ScraperAttributes(
            destination=destination,
            scrape_configuration=scrape_configuration,
            scraper_arn=scraper_arn,
            source=source,
            alias=alias,
            role_configuration=role_configuration,
        )

        return typing.cast("IScraper", jsii.sinvoke(cls, "fromScraperAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="isScraper")
    @builtins.classmethod
    def is_scraper(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__34e6af43e419cebdae94e53a8eb7f2112edcf143a28894ce155d8f3be94b5f49)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isScraper", [x]))

    @builtins.property
    @jsii.member(jsii_name="destination")
    def destination(self) -> "Destination":
        '''The Amazon Managed Service for Prometheus workspace the scraper sends metrics to.'''
        return typing.cast("Destination", jsii.get(self, "destination"))

    @builtins.property
    @jsii.member(jsii_name="scrapeConfiguration")
    def scrape_configuration(self) -> "ScrapeConfiguration":
        '''The configuration in use by the scraper.'''
        return typing.cast("ScrapeConfiguration", jsii.get(self, "scrapeConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="scraperArn")
    def scraper_arn(self) -> builtins.str:
        '''The ARN of the scraper.'''
        return typing.cast(builtins.str, jsii.get(self, "scraperArn"))

    @builtins.property
    @jsii.member(jsii_name="scraperId")
    def scraper_id(self) -> builtins.str:
        '''The ID of the scraper.'''
        return typing.cast(builtins.str, jsii.get(self, "scraperId"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "Source":
        '''The Amazon EKS cluster from which the scraper collects metrics.'''
        return typing.cast("Source", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''An optional user-assigned scraper alias.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="roleConfiguration")
    def role_configuration(self) -> typing.Optional["RoleConfiguration"]:
        '''The role configuration in an Amazon Managed Service for Prometheus scraper.'''
        return typing.cast(typing.Optional["RoleConfiguration"], jsii.get(self, "roleConfiguration"))


class Workspace(
    WorkspaceBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_aps.Workspace",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        alert_manager_definition: typing.Optional[builtins.str] = None,
        alias: typing.Optional[builtins.str] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        query_logging_configuration: typing.Optional[typing.Union["QueryLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        workspace_configuration: typing.Optional[typing.Union["WorkspaceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param alert_manager_definition: The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.
        :param alias: The alias that is assigned to this workspace to help identify it. It does not need to be unique. 0 to 100 characters
        :param kms_key: The customer managed AWS KMS key to use for encrypting data within your workspace.
        :param logging_configuration: Contains information about the current rules and alerting logging configuration for the workspace. Note: These logging configurations are only for rules and alerting logs.
        :param query_logging_configuration: The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.
        :param workspace_configuration: Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fce396480613eba99c44ddbc02181012d71649d36c3a0187e9437c5268bc1cd8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = WorkspaceProps(
            alert_manager_definition=alert_manager_definition,
            alias=alias,
            kms_key=kms_key,
            logging_configuration=logging_configuration,
            query_logging_configuration=query_logging_configuration,
            workspace_configuration=workspace_configuration,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromWorkspaceAttributes")
    @builtins.classmethod
    def from_workspace_attributes(
        cls,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        workspace_arn: builtins.str,
        alert_manager_definition: typing.Optional[builtins.str] = None,
        alias: typing.Optional[builtins.str] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        query_logging_configuration: typing.Optional[typing.Union["QueryLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        workspace_configuration: typing.Optional[typing.Union["WorkspaceConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> "IWorkspace":
        '''
        :param scope: -
        :param id: -
        :param workspace_arn: The arn of this workspace.
        :param alert_manager_definition: The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.
        :param alias: The alias that is assigned to this workspace to help identify it. It does not need to be unique.
        :param kms_key: The customer managed AWS KMS key to use for encrypting data within your workspace.
        :param logging_configuration: Contains information about the current rules and alerting logging configuration for the workspace. Note: These logging configurations are only for rules and alerting logs.
        :param query_logging_configuration: The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.
        :param workspace_configuration: Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__06e9f0a4ada069956fea79835fad029b7339fca1059f54a6118f01854e5e44ed)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = WorkspaceAttributes(
            workspace_arn=workspace_arn,
            alert_manager_definition=alert_manager_definition,
            alias=alias,
            kms_key=kms_key,
            logging_configuration=logging_configuration,
            query_logging_configuration=query_logging_configuration,
            workspace_configuration=workspace_configuration,
        )

        return typing.cast("IWorkspace", jsii.sinvoke(cls, "fromWorkspaceAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="isWorkspace")
    @builtins.classmethod
    def is_workspace(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fe05f7c3509dfbf0a171e57ba19ea445d159aeb564d5e5a1ee5815df73224518)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isWorkspace", [x]))

    @builtins.property
    @jsii.member(jsii_name="prometheusEndpoint")
    def prometheus_endpoint(self) -> builtins.str:
        '''The Prometheus endpoint available for this workspace..'''
        return typing.cast(builtins.str, jsii.get(self, "prometheusEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="workspaceArn")
    def workspace_arn(self) -> builtins.str:
        '''The ARN of the workspace.'''
        return typing.cast(builtins.str, jsii.get(self, "workspaceArn"))

    @builtins.property
    @jsii.member(jsii_name="workspaceId")
    def workspace_id(self) -> builtins.str:
        '''The unique ID for the workspace.'''
        return typing.cast(builtins.str, jsii.get(self, "workspaceId"))

    @builtins.property
    @jsii.member(jsii_name="alertManagerDefinition")
    def alert_manager_definition(self) -> typing.Optional[builtins.str]:
        '''The alert manager definition, a YAML configuration for the alert manager in your Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alertManagerDefinition"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        '''The alias that is assigned to this workspace to help identify it.

        It does not need to be
        unique.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The customer managed AWS KMS key to use for encrypting data within your workspace.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''Contains information about the current rules and alerting logging configuration for the workspace.

        Note: These logging configurations are only for rules and alerting logs.
        '''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="queryLoggingConfiguration")
    def query_logging_configuration(
        self,
    ) -> typing.Optional["QueryLoggingConfiguration"]:
        '''The definition of logging configuration in an Amazon Managed Service for Prometheus workspace.'''
        return typing.cast(typing.Optional["QueryLoggingConfiguration"], jsii.get(self, "queryLoggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="workspaceConfiguration")
    def workspace_configuration(self) -> typing.Optional["WorkspaceConfiguration"]:
        '''Use this structure to define label sets and the ingestion limits for time series that match label sets, and to specify the retention period of the workspace.'''
        return typing.cast(typing.Optional["WorkspaceConfiguration"], jsii.get(self, "workspaceConfiguration"))


class AnomalyDetector(
    AnomalyDetectorBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_aps.AnomalyDetector",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        alias: builtins.str,
        configuration: typing.Union["AnomalyDetectorConfiguration", typing.Dict[builtins.str, typing.Any]],
        workspace: "IWorkspace",
        evaluation_interval_in_seconds: typing.Optional[jsii.Number] = None,
        labels: typing.Optional[typing.Sequence[typing.Union["Label", typing.Dict[builtins.str, typing.Any]]]] = None,
        missing_data_action: typing.Optional[typing.Union["MissingDataAction", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param alias: The user-friendly name of the anomaly detector. 1 to 128 characters length.
        :param configuration: The algorithm configuration of the anomaly detector.
        :param workspace: An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.
        :param evaluation_interval_in_seconds: The frequency, in seconds, at which the anomaly detector evaluates metrics. Minimum value of 30. Maximum value of 86400.
        :param labels: The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector. Map Entries: Minimum number of 0 items. Maximum number of 140 items. Key Length Constraints: Minimum length of 1. Maximum length of 7168. Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]* Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        :param missing_data_action: The action taken when data is missing during evaluation.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e9cf951baecb48090e806ba79cfa6dec111ec6ec0305bb1c72f18f7e5a6cc4f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AnomalyDetectorProps(
            alias=alias,
            configuration=configuration,
            workspace=workspace,
            evaluation_interval_in_seconds=evaluation_interval_in_seconds,
            labels=labels,
            missing_data_action=missing_data_action,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="isAnomalyDetector")
    @builtins.classmethod
    def is_anomaly_detector(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5a92d8e3a483a119470088f310c1ea46fcbcafd285ccfeed903da2461af3188)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isAnomalyDetector", [x]))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> builtins.str:
        '''The user-friendly name of the anomaly detector. 1 to 64 characters length.

        Minimum length of 1. Maximum length of 64.
        Pattern: [0-9A-Za-z][-.0-9A-Z_a-z]*
        '''
        return typing.cast(builtins.str, jsii.get(self, "alias"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectorArn")
    def anomaly_detector_arn(self) -> builtins.str:
        '''The Amazon Resource Name (ARN) of the anomaly detector.'''
        return typing.cast(builtins.str, jsii.get(self, "anomalyDetectorArn"))

    @builtins.property
    @jsii.member(jsii_name="configuration")
    def configuration(self) -> "AnomalyDetectorConfiguration":
        '''The algorithm configuration of the anomaly detector.'''
        return typing.cast("AnomalyDetectorConfiguration", jsii.get(self, "configuration"))

    @builtins.property
    @jsii.member(jsii_name="workspace")
    def workspace(self) -> "IWorkspace":
        '''An Amazon Managed Service for Prometheus workspace is a logical and isolated Prometheus server dedicated to ingesting, storing, and querying your Prometheus-compatible metrics.'''
        return typing.cast("IWorkspace", jsii.get(self, "workspace"))

    @builtins.property
    @jsii.member(jsii_name="evaluationIntervalInSeconds")
    def evaluation_interval_in_seconds(self) -> typing.Optional[jsii.Number]:
        '''The frequency, in seconds, at which the anomaly detector evaluates metrics.

        Minimum value of 30. Maximum value of 86400.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "evaluationIntervalInSeconds"))

    @builtins.property
    @jsii.member(jsii_name="labels")
    def labels(self) -> typing.Optional[typing.List["Label"]]:
        '''The Amazon Managed Service for Prometheus metric labels associated with the anomaly detector.

        Map Entries: Minimum number of 0 items. Maximum number of 140 items.
        Key Length Constraints: Minimum length of 1. Maximum length of 7168.
        Key Pattern: (?!__)[a-zA-Z_][a-zA-Z0-9_]*
        Value Length Constraints: Minimum length of 1. Maximum length of 7168.
        '''
        return typing.cast(typing.Optional[typing.List["Label"]], jsii.get(self, "labels"))

    @builtins.property
    @jsii.member(jsii_name="missingDataAction")
    def missing_data_action(self) -> typing.Optional["MissingDataAction"]:
        '''The action taken when data is missing during evaluation.'''
        return typing.cast(typing.Optional["MissingDataAction"], jsii.get(self, "missingDataAction"))


__all__ = [
    "AmpConfiguration",
    "AnomalyDetector",
    "AnomalyDetectorBase",
    "AnomalyDetectorConfiguration",
    "AnomalyDetectorProps",
    "CloudWatchLogDestination",
    "Destination",
    "EksConfiguration",
    "IAnomalyDetector",
    "IResourcePolicy",
    "IRuleGroupsNamespace",
    "IScraper",
    "IWorkspace",
    "IgnoreNearExpected",
    "Label",
    "LimitsPerLabelSet",
    "LimitsPerLabelSetEntry",
    "LoggingConfiguration",
    "LoggingDestination",
    "LoggingFilter",
    "MissingDataAction",
    "QueryLoggingConfiguration",
    "RandomCutForestConfiguration",
    "ResourcePolicy",
    "ResourcePolicyBase",
    "ResourcePolicyProps",
    "RoleConfiguration",
    "RuleGroupsNamespace",
    "RuleGroupsNamespaceAttributes",
    "RuleGroupsNamespaceBase",
    "RuleGroupsNamespaceProps",
    "ScrapeConfiguration",
    "Scraper",
    "ScraperAttributes",
    "ScraperBase",
    "ScraperProps",
    "Source",
    "Workspace",
    "WorkspaceAttributes",
    "WorkspaceBase",
    "WorkspaceConfiguration",
    "WorkspaceProps",
]

publication.publish()

def _typecheckingstub__9b57f1ed441699407024d3a67f6d0ecf1fd33175a38d466e4e90e190923b70a0(
    *,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__488e50421526d1e316a7bd2f186eccb1fc4bf1daba066e779c147e9e9dbc747a(
    *,
    random_cut_forest: typing.Union[RandomCutForestConfiguration, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d73bc4f90dcbc90f45d5d011fc423d2638eb9cfe65810e23594184c620ce38aa(
    *,
    alias: builtins.str,
    configuration: typing.Union[AnomalyDetectorConfiguration, typing.Dict[builtins.str, typing.Any]],
    workspace: IWorkspace,
    evaluation_interval_in_seconds: typing.Optional[jsii.Number] = None,
    labels: typing.Optional[typing.Sequence[typing.Union[Label, typing.Dict[builtins.str, typing.Any]]]] = None,
    missing_data_action: typing.Optional[typing.Union[MissingDataAction, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4c8d116f44cd0ce0c010e39612b1f9f3d190e82d3f5f4c0372ae03517a31a79(
    *,
    log_group: _aws_cdk_aws_logs_ceddda9d.ILogGroup,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f247dc1883eff5c9525a2e09081bf65d9f34dc7f9581f5fcb643b104e14afa09(
    *,
    amp_configuration: typing.Union[AmpConfiguration, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9e3526038ce65e3714e7b69cac8f1dac03b300f7ee7b6eb0a81f578bb9386261(
    *,
    cluster: _aws_cdk_aws_eks_ceddda9d.ICluster,
    subnets: typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet],
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa12ec68028f74d5d8f1d96a0b99090659c404c86bd0ec936014ab264467ca22(
    *,
    amount: typing.Optional[jsii.Number] = None,
    ratio: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c797aa51820ba19e3974b523e246d357e3b44ff0bc743b0f1171b5ae9bebdea(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6893b1308b220935b9f1ce7c4eae4ddc73c29be6663d247911732ccfcec7f4d9(
    *,
    label_set: typing.Sequence[typing.Union[Label, typing.Dict[builtins.str, typing.Any]]],
    limits: typing.Union[LimitsPerLabelSetEntry, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f53acc1bbc1fb66aa75ed0ff80395c4fd66be1563ee572788afab4e42af12da4(
    *,
    max_series: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__282c7cd599e82904024934838ca325999d8149f211c5885145973734c9c85b76(
    *,
    log_group: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2496000b19af109fb0c5c290e32ab9bbc75be51fbfa27d16758c01f8baf00891(
    *,
    cloud_watch_logs: typing.Union[CloudWatchLogDestination, typing.Dict[builtins.str, typing.Any]],
    filters: typing.Union[LoggingFilter, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7beea1121128e5f35f0720b90b21713abba4beef8755e891bbf87c2ad9711a0(
    *,
    qsp_threshold: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4de31fdb80b9646037b68b88ae1dae6b46be704ab84a3c61100b29e91fc959c2(
    *,
    mark_as_anomaly: typing.Optional[builtins.bool] = None,
    skip: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__092820c29e1435155b193e5488fd2841dcea5141110ab984fa14a237e2f4a4ae(
    *,
    destinations: typing.Sequence[typing.Union[LoggingDestination, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c44dedd708a153df90c20f2738e66c34f510bb7ed036637ccb7a1bde1f3394b8(
    *,
    query: builtins.str,
    ignore_near_expected_from_above: typing.Optional[typing.Union[IgnoreNearExpected, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_near_expected_from_below: typing.Optional[typing.Union[IgnoreNearExpected, typing.Dict[builtins.str, typing.Any]]] = None,
    sample_size: typing.Optional[jsii.Number] = None,
    shingle_size: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1705a6716ddb826f74670d4b351789ae363cbbc6a4fda6389f3fe972e4ad37e8(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e64bdaac8096e1f570bf3bdd34320a336689a41b7fadad148bbe26533f682a36(
    *,
    policy_document: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e96c135bdcece9823caf073421082af151c59b6d52a5918bb38689bbca7ab2a3(
    *,
    source_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    target_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aca59ceb33a6b456771bcbba45d97752cb2f2f13917c19b7e97cd69b7f165a45(
    *,
    data: builtins.str,
    name: builtins.str,
    rule_groups_namespace_arn: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54435341b8b1c3c7efe004b41ef5c6d515fe3983bc74fae1b1b26947b9d05f20(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__38cadfd9b05a1407d50e98748f6488d0e79d3484e75c5786ea83b3235d73c3e1(
    *,
    data: builtins.str,
    name: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6313d0a5d8e3eda66be90025eafb5520d36fb7fb11adbc40c4398cb56b0ce09d(
    *,
    configuration_blob: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2aab74937b2fefec81fb3f25317393581e00fbda88f9d176c61fd521a9189d81(
    *,
    destination: typing.Union[Destination, typing.Dict[builtins.str, typing.Any]],
    scrape_configuration: typing.Union[ScrapeConfiguration, typing.Dict[builtins.str, typing.Any]],
    scraper_arn: builtins.str,
    source: typing.Union[Source, typing.Dict[builtins.str, typing.Any]],
    alias: typing.Optional[builtins.str] = None,
    role_configuration: typing.Optional[typing.Union[RoleConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__79f44dd804edbb4f2d30815f15d40d8f8c94bc90ec7657ced6d4b8716930412f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__720023f01199e16b0b50b3928b380b6c70d0c625eb677c6631c94d1822effb36(
    scraper_arn: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e27ba8269266aa91c926829a5c485aaf203a6638ce54c2fced4fdf950ba2e944(
    *,
    destination: typing.Union[Destination, typing.Dict[builtins.str, typing.Any]],
    scrape_configuration: typing.Union[ScrapeConfiguration, typing.Dict[builtins.str, typing.Any]],
    source: typing.Union[Source, typing.Dict[builtins.str, typing.Any]],
    alias: typing.Optional[builtins.str] = None,
    role_configuration: typing.Optional[typing.Union[RoleConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f45388bb39e3b47ec674e4da970163a87c5fb85665ad1fc10517bafda034ad5(
    *,
    eks_configuration: typing.Union[EksConfiguration, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bbfa4d3de7b456e3faeccf136f83095036d68c2058e82076f7a678eeac164e17(
    *,
    workspace_arn: builtins.str,
    alert_manager_definition: typing.Optional[builtins.str] = None,
    alias: typing.Optional[builtins.str] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    query_logging_configuration: typing.Optional[typing.Union[QueryLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    workspace_configuration: typing.Optional[typing.Union[WorkspaceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26324cd5062f2f5ec83013af6d021bcb8f2e2c6d4df14147a97bf35d099c4a1b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3ac750f120961e0958cd690a53ccc4e09d55d88803a7e53ed9bc1e70a3a9a78(
    workspace_arn: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae4d82a0bb8d7f12fbf4cbe9ccc1b9bdb2415b0517e902e2bdbf5e5546c092ce(
    *,
    limits_per_label_sets: typing.Optional[typing.Sequence[typing.Union[LimitsPerLabelSet, typing.Dict[builtins.str, typing.Any]]]] = None,
    retention_period_in_days: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__204cf0cc18e2fd2c643a33020d11a1d61cbfe8a2abd5cd5bda6a222e017e12ef(
    *,
    alert_manager_definition: typing.Optional[builtins.str] = None,
    alias: typing.Optional[builtins.str] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    query_logging_configuration: typing.Optional[typing.Union[QueryLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    workspace_configuration: typing.Optional[typing.Union[WorkspaceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__763ce8aef513d695a9ea5e157a4299be537296b8475d4cac315b4f595f7d0536(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__152018d2f86ee27c3ac817bf409dc2fae4034315290b87fd5d6c906625b633d3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    policy_document: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b7b7c7ca19cd491541f3243572cf47da8425bab13c98330c2653c2302cfa6b53(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d20ad42e4be3f2ea717b0a2a018087c9c8a4437ea677e47f420ba1b0b9d445d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    data: builtins.str,
    name: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07bf6a97084316812dac20b3c71ddb45a75f79b4a8ec626bd6762069ada7d925(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    data: builtins.str,
    name: builtins.str,
    rule_groups_namespace_arn: builtins.str,
    workspace: IWorkspace,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9f121730976c1abb9dd8b8aeb3d4783892a3f693e887909348c16a32681593f4(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__420a8a3c500b6acbf7b84e9b716db0e0256ad4fe2f714daf764abfebb254c38a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    destination: typing.Union[Destination, typing.Dict[builtins.str, typing.Any]],
    scrape_configuration: typing.Union[ScrapeConfiguration, typing.Dict[builtins.str, typing.Any]],
    source: typing.Union[Source, typing.Dict[builtins.str, typing.Any]],
    alias: typing.Optional[builtins.str] = None,
    role_configuration: typing.Optional[typing.Union[RoleConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a782eecfe3a632aac5c0103f9029c7ec8a0b5f2ac8b500e9a0257a762eda243d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    destination: typing.Union[Destination, typing.Dict[builtins.str, typing.Any]],
    scrape_configuration: typing.Union[ScrapeConfiguration, typing.Dict[builtins.str, typing.Any]],
    scraper_arn: builtins.str,
    source: typing.Union[Source, typing.Dict[builtins.str, typing.Any]],
    alias: typing.Optional[builtins.str] = None,
    role_configuration: typing.Optional[typing.Union[RoleConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__34e6af43e419cebdae94e53a8eb7f2112edcf143a28894ce155d8f3be94b5f49(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fce396480613eba99c44ddbc02181012d71649d36c3a0187e9437c5268bc1cd8(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    alert_manager_definition: typing.Optional[builtins.str] = None,
    alias: typing.Optional[builtins.str] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    query_logging_configuration: typing.Optional[typing.Union[QueryLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    workspace_configuration: typing.Optional[typing.Union[WorkspaceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__06e9f0a4ada069956fea79835fad029b7339fca1059f54a6118f01854e5e44ed(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    workspace_arn: builtins.str,
    alert_manager_definition: typing.Optional[builtins.str] = None,
    alias: typing.Optional[builtins.str] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    query_logging_configuration: typing.Optional[typing.Union[QueryLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    workspace_configuration: typing.Optional[typing.Union[WorkspaceConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe05f7c3509dfbf0a171e57ba19ea445d159aeb564d5e5a1ee5815df73224518(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8e9cf951baecb48090e806ba79cfa6dec111ec6ec0305bb1c72f18f7e5a6cc4f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    alias: builtins.str,
    configuration: typing.Union[AnomalyDetectorConfiguration, typing.Dict[builtins.str, typing.Any]],
    workspace: IWorkspace,
    evaluation_interval_in_seconds: typing.Optional[jsii.Number] = None,
    labels: typing.Optional[typing.Sequence[typing.Union[Label, typing.Dict[builtins.str, typing.Any]]]] = None,
    missing_data_action: typing.Optional[typing.Union[MissingDataAction, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5a92d8e3a483a119470088f310c1ea46fcbcafd285ccfeed903da2461af3188(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

for cls in [IAnomalyDetector, IResourcePolicy, IRuleGroupsNamespace, IScraper, IWorkspace]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
