# dpps

![Version: 0.0.0-dev](https://img.shields.io/badge/Version-0.0.0--dev-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.0.0-dev](https://img.shields.io/badge/AppVersion-0.0.0--dev-informational?style=flat-square)

A Helm chart for the DPPS project

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| The DPPS Authors | <dpps@cta-observatory.com> |  |

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://fluent.github.io/helm-charts | fluent-bit | 0.48.9 |
| https://grafana.github.io/helm-charts | grafana | 9.2.2 |
| https://grafana.github.io/helm-charts | loki | 6.30.1 |
| https://prometheus-community.github.io/helm-charts | prometheus | 27.20.0 |
| oci://harbor.cta-observatory.org/dpps | bdms | v0.6.0 |
| oci://harbor.cta-observatory.org/dpps | iam(dpps-iam) | v0.1.2 |
| oci://harbor.cta-observatory.org/dpps | gcert-issuer | v0.1.0 |
| oci://harbor.cta-observatory.org/dpps | qualpipe-webapp | v0.2.0-rc1 |
| oci://harbor.cta-observatory.org/dpps | simpipe | v0.3.0 |
| oci://harbor.cta-observatory.org/dpps | wms | v0.5.2 |
| oci://harbor.cta-observatory.org/proxy_cache/bitnamicharts | mariadb | 20.5.5 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| alias_svc.dirac_db.enabled | bool | `true` |  |
| alias_svc.dpps_fts.enabled | bool | `false` |  |
| alias_svc.dpps_iam.enabled | bool | `true` |  |
| alias_svc.dpps_mariadb.enabled | bool | `false` |  |
| alias_svc.dpps_minio.enabled | bool | `false` |  |
| bdms.acada_ingest.workers.enabled | bool | `false` |  |
| bdms.cert-generator-grid.enabled | bool | `false` |  |
| bdms.configure_test_setup | bool | `true` |  |
| bdms.enabled | bool | `true` | Whether to deploy BDMS |
| bdms.gcert-issuer.enabled | bool | `false` |  |
| bdms.iam.enabled | bool | `false` |  |
| bdms.prepuller_enabled | bool | `false` |  |
| bdms.redis.enabled | bool | `false` |  |
| bdms.rucio-daemons.ftsRenewal.servers | string | `"https://dpps-fts:8446"` |  |
| bdms.rucio_iam_sync_user.enabled | bool | `true` |  |
| bdms.rucio_iam_sync_user.iam_server | string | `"http://{{ .Release.Name }}-iam-login-service:8080"` |  |
| bdms.rucio_iam_sync_user.secret.client_id | string | `"dpps-test-client"` |  |
| bdms.rucio_iam_sync_user.secret.client_secret | string | `"secret"` |  |
| bdms.rucio_iam_sync_user.secret.create | bool | `true` | Create secret from values, for testing. Set to false for production and create secret |
| bdms.rucio_iam_sync_user.secret.name | string | `"sync-rucio-iam-config"` | name of the secret containing the sync config file in key sync-iam-rucio.cfg |
| bdms.safe_to_bootstrap_rucio | bool | `true` |  |
| cert-generator-grid.enabled | bool | `false` |  |
| dev.client_image_tag | string | `nil` | tag of the image used to run helm tests |
| dev.mount_repo | bool | `true` | mount the repo volume to test the code as it is being developed |
| dev.n_test_jobs | int | `1` | number of parallel test jobs for pytest |
| dev.pipelines | object | `{"calibpipe":{"version":"v0.4.0"},"datapipe":{"version":"v0.3.1"}}` | Pipelines versions used in the tests |
| dev.runAsGroup | int | `1000` |  |
| dev.runAsUser | int | `1000` | user to run the container as. needs to be the same as local user if writing to repo directory |
| dev.run_tests | bool | `true` | run tests in the container |
| dev.sleep | bool | `false` | sleep after test to allow interactive development |
| dev.start_long_running_client | bool | `false` | if true, a long-running client container will start *instead* of a test container |
| fluent-bit.config.inputs | string | `"[INPUT]\n    Name tail\n    Path /var/log/containers/*.log\n    multiline.parser docker, cri\n    Tag kube.*\n    Mem_Buf_Limit 5MB\n    Buffer_Chunk_Size 1\n    Refresh_Interval 1\n    Skip_Long_Lines On\n"` |  |
| fluent-bit.config.outputs | string | `"[FILTER]\n    Name grep\n    Match *\n\n[OUTPUT]\n    Name        loki\n    Match       *\n    Host        {{ .Release.Name }}-loki-gateway\n    port        80\n    tls         off\n    tls.verify  off\n"` |  |
| fluent-bit.config.rbac.create | bool | `true` |  |
| fluent-bit.config.rbac.eventsAccess | bool | `true` |  |
| fluent-bit.enabled | bool | `true` |  |
| fluent-bit.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/fluent/fluent-bit"` |  |
| fluent-bit.testFramework.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/busybox"` |  |
| gcert-issuer.bootstrap_job.enabled | bool | `true` |  |
| gcert-issuer.dev.mount_repo | bool | `false` |  |
| gcert-issuer.enabled | bool | `true` |  |
| gcert-issuer.iam.enabled | bool | `false` |  |
| gcert-issuer.iam_sync.default_namespace | string | `"cta-dpps"` |  |
| gcert-issuer.iam_sync.enabled | bool | `true` |  |
| gcert-issuer.use_checksum | bool | `false` |  |
| global.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| global.security.allowInsecureImages | bool | `true` |  |
| grafana.adminPassword | string | `"admin"` |  |
| grafana.adminUser | string | `"admin"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".apiVersion | int | `1` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[0].editable | bool | `true` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[0].name | string | `"default"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[0].options.path | string | `"/var/lib/grafana/dashboards/default"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[0].type | string | `"file"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[1].editable | bool | `true` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[1].name | string | `"sidecar"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[1].options.path | string | `"/var/lib/grafana/dashboards/sidecar"` |  |
| grafana.dashboardProviders."dashboardproviders.yaml".providers[1].type | string | `"file"` |  |
| grafana.dashboards.default.k8-views-global.datasource | string | `"Prometheus"` |  |
| grafana.dashboards.default.k8-views-global.gnetId | int | `15757` |  |
| grafana.dashboards.default.k8-views-global.revision | int | `43` |  |
| grafana.dashboards.default.k8-views-namespaces.datasource | string | `"Prometheus"` |  |
| grafana.dashboards.default.k8-views-namespaces.gnetId | int | `15758` |  |
| grafana.dashboards.default.k8-views-namespaces.revision | int | `42` |  |
| grafana.dashboards.default.k8-views-nodes.datasource | string | `"Prometheus"` |  |
| grafana.dashboards.default.k8-views-nodes.gnetId | int | `15759` |  |
| grafana.dashboards.default.k8-views-nodes.revision | int | `37` |  |
| grafana.dashboards.default.k8-views-pods.datasource | string | `"Prometheus"` |  |
| grafana.dashboards.default.k8-views-pods.gnetId | int | `15760` |  |
| grafana.dashboards.default.k8-views-pods.revision | int | `36` |  |
| grafana.datasources."datasources.yaml".apiVersion | int | `1` |  |
| grafana.datasources."datasources.yaml".datasources[0].access | string | `"proxy"` |  |
| grafana.datasources."datasources.yaml".datasources[0].name | string | `"Prometheus"` |  |
| grafana.datasources."datasources.yaml".datasources[0].type | string | `"prometheus"` |  |
| grafana.datasources."datasources.yaml".datasources[0].url | string | `"http://dpps-prometheus-server"` |  |
| grafana.datasources."datasources.yaml".datasources[1].access | string | `"proxy"` |  |
| grafana.datasources."datasources.yaml".datasources[1].jsonData.maxLines | int | `1000` |  |
| grafana.datasources."datasources.yaml".datasources[1].jsonData.timeout | int | `60` |  |
| grafana.datasources."datasources.yaml".datasources[1].name | string | `"Loki"` |  |
| grafana.datasources."datasources.yaml".datasources[1].type | string | `"loki"` |  |
| grafana.datasources."datasources.yaml".datasources[1].url | string | `"http://dpps-loki:3100"` |  |
| grafana.downloadDashboardsImage.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| grafana.enabled | bool | `true` |  |
| grafana.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| grafana.ingress.enabled | bool | `true` |  |
| grafana.ingress.hosts[0] | string | `"grafana.dpps.local"` |  |
| grafana.persistentVolume.size | string | `"100Mi"` |  |
| grafana.prometheus-node-exporter.enabled | bool | `false` |  |
| grafana.retention | string | `"1d"` |  |
| grafana.sidecar.dashboards.defaultFolderName | string | `"Sidecar Dashboards"` |  |
| grafana.sidecar.dashboards.enabled | bool | `true` |  |
| grafana.sidecar.dashboards.folder | string | `"/var/lib/grafana/dashboards/sidecar"` |  |
| grafana.sidecar.dashboards.folderAnnotation | string | `"grafana_folder"` |  |
| grafana.sidecar.dashboards.provider.name | string | `"sidecar"` |  |
| grafana.sidecar.dashboards.searchNamespace | string | `"ALL"` |  |
| grafana.sidecar.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| grafana.testFramework.enabled | bool | `false` |  |
| iam.dev.mount_repo | bool | `false` |  |
| iam.dppsTrustStore.CABundlePVCName | string | `"{{ include \"dpps-iam.fullname\" . }}-ca-bundle-pvc"` |  |
| iam.dppsTrustStore.enabled | bool | `true` |  |
| iam.dppsTrustStore.gridCABundlePVCName | string | `"{{ include \"dpps-iam.fullname\" . }}-grid-ca-bundle-pvc"` |  |
| iam.dppsTrustStore.initJob.asHook | bool | `true` |  |
| iam.enabled | bool | `true` |  |
| iam.iam.database.external.existingSecret | string | `""` |  |
| iam.iam.database.external.host | string | `"dpps-mariadb"` |  |
| iam.iam.database.external.name | string | `"indigo-iam"` |  |
| iam.iam.database.external.password | string | `"PassW0rd"` |  |
| iam.iam.database.external.port | int | `3306` |  |
| iam.iam.database.external.username | string | `"indigo-iam"` |  |
| iam.iam.mariadb.enabled | bool | `false` |  |
| iam.iam.mysql.enabled | bool | `false` |  |
| image.pullPolicy | string | `"IfNotPresent"` |  |
| image.repository_prefix | string | `"harbor.cta-observatory.org/dpps/dpps"` |  |
| loki.backend.replicas | int | `0` |  |
| loki.bloomCompactor.replicas | int | `0` |  |
| loki.bloomGateway.replicas | int | `0` |  |
| loki.compactor.replicas | int | `0` |  |
| loki.deploymentMode | string | `"SingleBinary"` |  |
| loki.distributor.replicas | int | `0` |  |
| loki.enabled | bool | `true` |  |
| loki.indexGateway.replicas | int | `0` |  |
| loki.ingester.replicas | int | `0` |  |
| loki.loki.auth_enabled | bool | `false` |  |
| loki.loki.commonConfig.replication_factor | int | `1` |  |
| loki.loki.limits_config.allow_structured_metadata | bool | `true` |  |
| loki.loki.limits_config.volume_enabled | bool | `true` |  |
| loki.loki.pattern_ingester.enabled | bool | `true` |  |
| loki.loki.ruler.enable_api | bool | `true` |  |
| loki.loki.schemaConfig.configs[0].from | string | `"2024-04-01"` |  |
| loki.loki.schemaConfig.configs[0].index.period | string | `"24h"` |  |
| loki.loki.schemaConfig.configs[0].index.prefix | string | `"loki_index_"` |  |
| loki.loki.schemaConfig.configs[0].object_store | string | `"s3"` |  |
| loki.loki.schemaConfig.configs[0].schema | string | `"v13"` |  |
| loki.loki.schemaConfig.configs[0].store | string | `"tsdb"` |  |
| loki.loki.storage.bucketNames.admin | string | `"loki-admin"` |  |
| loki.loki.storage.bucketNames.chunks | string | `"loki-chunks"` |  |
| loki.loki.storage.bucketNames.ruler | string | `"loki-ruler"` |  |
| loki.loki.storage.s3.accessKeyId | string | `"rootuser"` |  |
| loki.loki.storage.s3.endpoint_url | string | `"http://dpps-minio:9000"` |  |
| loki.loki.storage.s3.insecure | bool | `true` |  |
| loki.loki.storage.s3.s3ForcePathStyle | bool | `true` |  |
| loki.loki.storage.s3.secretAccessKey | string | `"rootpass123"` |  |
| loki.loki.storage.type | string | `"s3"` |  |
| loki.memcached.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/memcached"` |  |
| loki.memcached.image.tag | string | `"1.6.38-alpine3.22"` |  |
| loki.memcachedExporter.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/prom/memcached-exporter"` |  |
| loki.minio.enabled | bool | `false` |  |
| loki.monitoring.selfMonitoring.enabled | bool | `false` |  |
| loki.monitoring.selfMonitoring.grafanaAgent.installOperator | bool | `false` |  |
| loki.monitoring.selfMonitoring.lokiCanary.enabled | bool | `false` |  |
| loki.querier.replicas | int | `0` |  |
| loki.queryFrontend.replicas | int | `0` |  |
| loki.queryScheduler.replicas | int | `0` |  |
| loki.read.replicas | int | `0` |  |
| loki.rollout_operator.enabled | bool | `false` |  |
| loki.sidecar.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/kiwigrid/k8s-sidecar"` |  |
| loki.singleBinary.replicas | int | `1` |  |
| loki.test.enabled | bool | `false` |  |
| loki.write.replicas | int | `0` |  |
| mariadb | object | `{"auth":{"rootPassword":"dirac-db-root"},"enabled":true,"image":{"registry":"harbor.cta-observatory.org/proxy_cache","repository":"bitnamilegacy/mariadb"},"initdbScripts":{"create-user.sql":"CREATE USER IF NOT EXISTS 'Dirac'@'%' IDENTIFIED BY 'dirac-db';\nCREATE USER IF NOT EXISTS 'indigo-iam'@'%' IDENTIFIED BY 'PassW0rd';\nCREATE DATABASE IF NOT EXISTS `indigo-iam`;\nGRANT ALL PRIVILEGES ON `indigo-iam`.* TO `indigo-iam`@`%`;\nFLUSH PRIVILEGES;\n"}}` | -- external DB for WMS and IAM use wms mariad-db subchart also as db for iam, avoids multiple mariadb servers and currently also naming conflicts with two mariadb charts active |
| prometheus.alertmanager.enabled | bool | `false` |  |
| prometheus.enabled | bool | `true` |  |
| prometheus.kube-state-metrics.image.registry | string | `"harbor.cta-observatory.org/proxy_k8s"` |  |
| prometheus.prometheus-node-exporter.image.registry | string | `"harbor.cta-observatory.org/proxy_cache"` |  |
| prometheus.prometheus-node-exporter.image.repository | string | `"prom/node-exporter"` |  |
| prometheus.prometheus-pushgateway.enabled | bool | `false` |  |
| prometheus.server.image.repository | string | `"harbor.cta-observatory.org/proxy_cache/prom/prometheus"` |  |
| qualpipe-webapp.enabled | bool | `true` |  |
| simpipe.enabled | bool | `false` |  |
| simpipe.mongodb.initdbScriptsConfigMap | string | `"dpps-simpipe-setup-mongodb-user"` |  |
| waitForMkfs.enabled | bool | `true` |  |
| wms | object | `{"cert-generator-grid":{"enabled":false},"cvmfs":{"enabled":true,"publish_docker_images":["harbor.cta-observatory.org/dpps/datapipe:v0.3.1","harbor.cta-observatory.org/dpps/calibpipe:v0.4.0"]},"diracServer":{"bootstrap":{"componentMonitoring":true,"enabled":true,"firstProxy":true,"image":"harbor.cta-observatory.org/proxy_cache/bitnamilegacy/kubectl:1.33.1","initDiracDb":true,"syncDiracxCS":true,"syncIamUsers":true,"syncRSS":true},"configurationName":"DPPS-Tests","diracComponents":{"_agentDefaults":{"port":null,"replicaCount":1,"type":"agent"},"_executorDefaults":{"port":null,"replicaCount":1,"type":"executor"},"_serviceDefaults":{"replicaCount":1,"type":"service"},"bundleDelivery":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/BundleDelivery","port":9158},"cleanReqDB":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"RequestManagement/CleanReqDBAgent","port":null},"componentMonitoring":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/ComponentMonitoring","port":9190},"fileCatalog":{"<<":{"replicaCount":1,"type":"service"},"cmd":"DataManagement/FileCatalog","port":9197},"jobManager":{"cmd":"WorkloadManagement/JobManager","port":9132,"replicaCount":1,"type":"service"},"jobMonitoring":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/JobMonitoring","port":9130},"jobStateUpdate":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/JobStateUpdate","port":9136},"matcher":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/Matcher","port":9170},"optimizationMind":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/OptimizationMind","port":9175},"optimizers":{"<<":{"port":null,"replicaCount":1,"type":"executor"},"cmd":"WorkloadManagement/Optimizers","port":null},"pilotManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/PilotManager","port":9171},"pilotStatus":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/PilotStatusAgent","port":null},"pilotSync":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/PilotSyncAgent","port":null},"proxyManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/ProxyManager","port":9152},"publisher":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/Publisher","port":9165},"reqExecuting":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"RequestManagement/RequestExecutingAgent","port":null},"reqManager":{"<<":{"replicaCount":1,"type":"service"},"cmd":"RequestManagement/ReqManager","port":9140},"reqProxy":{"<<":{"replicaCount":1,"type":"service"},"cmd":"RequestManagement/ReqProxy","port":9161},"resourceManagement":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/ResourceManagement","port":9172},"resourceStatus":{"<<":{"replicaCount":1,"type":"service"},"cmd":"ResourceStatus/ResourceStatus","port":9160},"sandboxStore":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/SandboxStore","port":9196},"siteDirector":{"<<":{"port":null,"replicaCount":1,"type":"agent"},"cmd":"WorkloadManagement/SiteDirector","port":null},"storageElement":{"<<":{"replicaCount":1,"type":"service"},"cmd":"DataManagement/StorageElement","port":9148},"systemAdmin":{"<<":{"replicaCount":1,"type":"service"},"cmd":"Framework/SystemAdministrator","port":9162},"wmsAdmin":{"<<":{"replicaCount":1,"type":"service"},"cmd":"WorkloadManagement/WMSAdministrator","port":9145}},"diracConfig":{"registry":{"DefaultGroup":"dirac_user","groups":{"dirac_admin":{"properties":["AlarmsManagement","ServiceAdministrator","CSAdministrator","JobAdministrator","FullDelegation","ProxyManagement","Operator"],"users":["admin-user"]},"dirac_user":{"properties":["NormalUser"],"users":["test-user"]},"dpps_genpilot":{"properties":["GenericPilot","LimitedDelegation"],"users":["admin-user"]},"dpps_group":{"properties":["NormalUser","PrivateLimitedDelegation"],"users":["admin-user","test-user"]}},"users":{"admin-user":{"CA":"/CN=DPPS Development CA","DN":"/CN=DPPS User"}}},"resources":{"fileCatalog":"\nRucioFileCatalog\n{\n  CatalogType = RucioFileCatalog\n  AccessType = Read-Write\n  Status = Active\n  Master = True\n  CatalogURL = DataManagement/FileCatalog\n  MetaCatalog = True\n}\n","sites":"CTAO\n{\n  CTAO.CI.de\n  {\n    Name = CTAO.CI.de\n    CE = dirac-ce\n    CEs\n    {\n      dirac-ce\n      {\n        CEType = SSH\n        SubmissionMode = Direct\n        SSHHost = dirac-ce\n        SSHUser = dirac\n        SSHKey = /home/dirac/.ssh/diracuser_sshkey\n        wnTmpDir = /tmp\n        Pilot = True\n        SharedArea = /home/dirac\n        UserEnvVariables = RUCIO_HOME:::/cvmfs/ctao.dpps.test/rucio\n        ExtraPilotOptions = --PollingTime 10 --CVMFS_locations=/\n        Queues\n        {\n          normal\n          {\n            maxCPUTime = 172800\n            SI00 = 2155\n            MaxTotalJobs = 2500\n            MaxWaitingJobs = 300\n            VO = ctao.dpps.test\n            BundleProxy = True\n          }\n        }\n      }\n    }\n    SE = STORAGE-1\n    SE += STORAGE-2\n    SE += STORAGE-3\n  }\n\n}\n","storageElements":"\nSandboxSE\n{\n  BackendType = DISET\n  AccessProtocol.1\n  {\n    Host = {{ .Release.Name }}-wms-dirac-sandbox-store\n    Port = {{ .Values.diracServer.diracComponents.sandboxStore.port }}\n    PluginName = DIP\n    Protocol = dips\n    Path = /WorkloadManagement/SandboxStore\n    Access = remote\n    WSUrl =\n  }\n}\n\n\nSTORAGE-1 {\n  BackendType = xrootd\n  ReadAccess = Active\n  WriteAccess = Active\n  RemoveAccess = Active\n  AccessProtocol.1 {\n    Host = rucio-storage-1\n    Port = 1094\n    Protocol = root\n    Path = /rucio\n    Access = remote\n    SpaceToken =\n    WSUrl = /srm/managerv2?SFN=\n    PluginName = GFAL2_XROOT\n    ProtocolsList = file\n  }\n}\nSTORAGE-2 {\n  BackendType = xrootd\n  ReadAccess = Active\n  WriteAccess = Active\n  RemoveAccess = Active\n  AccessProtocol.1 {\n    Host = rucio-storage-2\n    Port = 1094\n    Protocol = root\n    Path = /rucio\n    Access = remote\n    SpaceToken =\n    WSUrl = /srm/managerv2?SFN=\n    PluginName = GFAL2_XROOT\n    ProtocolsList = file\n  }\n}\nSTORAGE-3 {\n  BackendType = xrootd\n  ReadAccess = Active\n  WriteAccess = Active\n  RemoveAccess = Active\n  AccessProtocol.1 {\n    Host = rucio-storage-3\n    Port = 1094\n    Protocol = root\n    Path = /rucio\n    Access = remote\n    SpaceToken =\n    WSUrl = /srm/managerv2?SFN=\n    PluginName = GFAL2_XROOT\n    ProtocolsList = file\n  }\n}\n"}},"diracDatabases":["AccountingDB","FileCatalogDB","InstalledComponentsDB","JobDB","JobLoggingDB","PilotAgentsDB","ProxyDB","ReqDB","ResourceManagementDB","ResourceStatusDB","SandboxMetadataDB","StorageManagementDB","TaskQueueDB"],"diracx":{"legacyExchangeApiKey":"diracx:legacy:Mr8ostGuB_SsdmcjZb7LPkMkDyp9rNuHX6w1qAqahDg="},"environment":{"DB_DIRAC_PASSWORD":"dirac-db","DB_ROOT_PASSWORD":"dirac-db-root","DIRAC_CFG_MASTER_CS":"/configurations/masterCS.cfg","DIRAC_CFG_PATH":"/configurations","DIRAC_X509_HOST_CERT":"/opt/dirac/etc/grid-security/hostcert.pem","DIRAC_X509_HOST_KEY":"/opt/dirac/etc/grid-security/hostkey.pem","X509_CERT_DIR":"/opt/dirac/etc/grid-security/certificates","X509_VOMSES":"/opt/dirac/etc/grid-security/vomses","X509_VOMS_DIR":"/opt/dirac/etc/grid-security/vomsdir"},"initContainers":{"certKeys":{"volumeMounts":[{"mountPath":"/home/dirac/.ssh","name":"ssh-dir"},{"mountPath":"/opt/dirac/etc/grid-security","name":"certs-dir"},{"mountPath":"/home/dirac/.globus","name":"globus-dir"}],"volumes":[{"emptyDir":{},"name":"ssh-dir"},{"emptyDir":{},"name":"globus-dir"},{"emptyDir":{},"name":"certs-dir"}]}},"masterCS":{"enabled":true,"extraVolumeMounts":null,"extraVolumes":null,"hostkey":{"secretFullName":""},"port":9135},"podAnnotations":{},"podLabels":{},"podSecurityContext":{},"resetDatabasesOnStart":["ResourceStatusDB","ProxyDB","JobDB","SandboxMetadataDB","TaskQueueDB","JobLoggingDB","PilotAgentsDB","ReqDB","AccountingDB","FileCatalogDB"],"securityContext":{},"voName":"ctao.dpps.test","volumeMounts":[],"volumes":[],"webApp":{"enabled":true,"extraVolumeMounts":null,"extraVolumes":null,"hostkey":{"secretFullName":""}}},"diracx":{"developer":{"enabled":true,"localCSPath":"/local_cs_store","urls":{"diracx":"http://dpps-diracx:8000","iam":"http://dpps-iam:8080","minio":"http://dpps-minio:32000"}},"dex":{"enabled":false},"diracx":{"hostname":"dpps-diracx","osDbs":{"dbs":{"JobParametersDB":null}},"settings":{"DIRACX_CONFIG_BACKEND_URL":"git+file:///cs_store/initialRepo","DIRACX_LEGACY_EXCHANGE_HASHED_API_KEY":"19628aa0cb14b69f75b2164f7fda40215be289f6e903d1acf77b54caed61a720","DIRACX_SANDBOX_STORE_AUTO_CREATE_BUCKET":"true","DIRACX_SANDBOX_STORE_BUCKET_NAME":"sandboxes","DIRACX_SANDBOX_STORE_S3_CLIENT_KWARGS":"{\"endpoint_url\": \"http://dpps-minio:9000\", \"aws_access_key_id\": \"rootuser\", \"aws_secret_access_key\": \"rootpass123\"}","DIRACX_SERVICE_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES":"120","DIRACX_SERVICE_AUTH_ALLOWED_REDIRECTS":"[\"http://wms-diracx:8000/api/docs/oauth2-redirect\", \"http://wms-diracx:8000/#authentication-callback\"]","DIRACX_SERVICE_AUTH_REFRESH_TOKEN_EXPIRE_MINUTES":"360","DIRACX_SERVICE_AUTH_TOKEN_ISSUER":"http://wms-diracx:8000","DIRACX_SERVICE_AUTH_TOKEN_KEYSTORE":"file:///keystore/jwks.json"},"sqlDbs":{"dbs":{"AuthDB":{"internalName":"DiracXAuthDB"},"JobDB":null,"JobLoggingDB":null,"SandboxMetadataDB":null,"TaskQueueDB":null},"default":{"host":"dpps-mariadb:3306","password":"dirac-db","rootPassword":"dirac-db-root","rootUser":"root","user":"Dirac"}},"startupProbe":{"failureThreshold":60,"periodSeconds":15,"timeoutSeconds":5}},"elasticsearch":{"enabled":false},"enabled":true,"global":{"activeDeadlineSeconds":900,"batchJobTTL":3600,"imagePullPolicy":"Always","images":{"client":"ghcr.io/diracgrid/diracx/client","services":"ghcr.io/diracgrid/diracx/services","tag":"v0.0.1a50"}},"grafana":{"enabled":false},"indigoiam":{"enabled":false},"initSql":{"enabled":false,"env":{}},"jaeger":{"enabled":false},"minio":{"environment":{"MINIO_BROWSER_REDIRECT_URL":"http://dpps-minio:32001/"},"image":{"repository":"harbor.cta-observatory.org/dpps/quay-io-minio-minio"},"mcImage":{"repository":"harbor.cta-observatory.org/dpps/quay-io-minio-mc"},"rootPassword":"rootpass123","rootUser":"rootuser"},"mysql":{"enabled":false},"opensearch":{"enabled":true},"opentelemetry-collector":{"enabled":false},"prometheus":{"enabled":false},"rabbitmq":{"auth":{"existingErlangSecret":"rabbitmq-secret","existingPasswordSecret":"rabbitmq-secret"},"containerSecurityContext":{"enabled":false},"enabled":true,"image":{"registry":"harbor.cta-observatory.org/proxy_cache","repository":"bitnamilegacy/rabbitmq"},"podSecurityContext":{"enabled":false}}},"enabled":true,"global":{"dockerRegistry":"harbor.cta-observatory.org/proxy_cache","images":{"busybox":{"repository":"harbor.cta-observatory.org/proxy_cache/busybox"}},"registry":"harbor.cta-observatory.org/proxy_cache"},"iam":{"bootstrap":{"config":{"clients":[{"client_id":"dpps-test-client","client_name":"WMS Test Client","client_secret":"secret","grant_types":["authorization_code","password","client_credentials","urn:ietf:params:oauth:grant_type:redelegate","refresh_token"],"redirect_uris":["http://wms-diracx:8000/api/auth/device/complete","http://wms-diracx:8000/api/auth/authorize/complete"],"scopes":["scim:write","scim:read","offline_access","openid","profile","iam:admin.write","iam:admin.read"]}],"issuer":"http://wms-dpps-iam-login-service:8080"}},"enabled":false},"iam_external":{"enabled":true,"loginServiceURL":"http://dpps-iam-login-service:8080"},"mariadb":{"enabled":false},"rucio":{"enabled":true,"rucioConfig":"{{ .Release.Name }}-bdms-rucio-config"},"test_ce":{"enabled":true}}` | WMS configuration |
| wms.diracServer.resetDatabasesOnStart | list | `["ResourceStatusDB","ProxyDB","JobDB","SandboxMetadataDB","TaskQueueDB","JobLoggingDB","PilotAgentsDB","ReqDB","AccountingDB","FileCatalogDB"]` | Recreates some DIRAC databases from scratch. Useful at first installation, but destructive on update: should be changed immediately after the first installation. This list might overlap with list of of DBs in chart/templates/configmap.yaml |
| wms.enabled | bool | `true` | Whether to deploy WMS |

