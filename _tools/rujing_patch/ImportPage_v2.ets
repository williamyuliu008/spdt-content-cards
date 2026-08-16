/**
 * 入境 APP · 导入页
 * 卡片包一键导入 + 视频包导入（IF-B 协议）
 *
 * v3 扩展（2026-07-20）：
 *   - 新增「墨骨山河全集」8集导入（23.8min, 27.4MB）
 *   - 新增国美书法校考卡包（18张/9链）
 *   - 新增历史 v3 卡片包（129张/16链）
 *   - 视频包：metadata 合并版（墨骨山河全集_metadata.json）
 */

import { router } from '@kit.ArkUI';
import { promptAction } from '@kit.ArkUI';
import { importCardPackage, importChainMeta, importVideoPackage, getVideoMeta, getVideoDir } from '../service/ImportService';
import { fileIo } from '@kit.CoreFileKit';
import { util } from '@kit.ArkTS';
import { BusinessError } from '@kit.BasicServicesKit';

@Entry
@Component
struct ImportPage {
  @State importResult: string = '';
  @State isImporting: boolean = false;
  @State importedCards: number = 0;
  @State importedChains: number = 0;
  @State videoImportResult: string = '';
  @State isVideoImporting: boolean = false;
  @State importedVideos: number = 0;
  @State importedSeries: string = '';
  @State moguImportResult: string = '';
  @State isMoguImporting: boolean = false;
  @State moguCards: number = 0;
  @State gaokaoImportResult: string = '';
  @State isGaokaoImporting: boolean = false;
  @State gaokaoCards: number = 0;
  @State gaokaoChains: number = 0;
  @State cafaImportResult: string = '';
  @State isCafaImporting: boolean = false;
  @State cafaCards: number = 0;
  @State cafaChains: number = 0;
  @State historyV3ImportResult: string = '';
  @State isHistoryV3Importing: boolean = false;
  @State historyV3Cards: number = 0;
  @State fullSeriesImportResult: string = '';
  @State isFullSeriesImporting: boolean = false;
  @State fullSeriesVideos: number = 0;
  @State fullSeriesDuration: string = '';
  // v2.1: /data/local/tmp/ 临时导入（hdc push 路径，spdt-content-cards 流）
  @State tempImportResult: string = '';
  @State isTempImporting: boolean = false;
  @State tempImportedCards: number = 0;
  @State tempImportedChains: number = 0;

  build() {
    Column() {
      Row() {
        Text('← 返回首页')
          .fontSize(15).fontColor('#4a6cf7')
          .onClick(() => router.pushUrl({ url: 'pages/Index' }))
        Blank()
        Text('导入数据')
          .fontSize(18).fontWeight(600).fontColor('#1a1a1a')
      }
      .width('100%').padding({ left: 16, right: 16, top: 16, bottom: 12 })

      Scroll() {
        Column({ space: 20 }) {
          // ── 视频包导入区块（IF-B，v2）───────────────────────
          Column() {
            Row() {
              Text('视频包导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' IF-B v1.0 ')
                .fontSize(11).fontColor('#4a6cf7')
                .backgroundColor('#f0f4ff')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('从 metadata.json 导入视频包元数据（scene_timeline / 五蕴）')
              .fontSize(12).fontColor('#888').margin({ top: 4 })

            Text('从 App 内置资源导入（无需外部文件）')
              .fontSize(12).fontColor('#888').margin({ top: 8 })
            Text('ep06_metadata.json → 墨骨山河_ep06（李斯·小篆统一）')
              .fontSize(11).fontColor('#5B8C5A')
              .backgroundColor('#f0fdf4').borderRadius(6)
              .padding(8).width('100%').margin({ top: 4 })

            Column() {
              Text('开始导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入视频包')
                .fontSize(14).backgroundColor('#4a6cf7').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doVideoImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#f0f7ff').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.videoImportResult.length > 0) {
            Column() {
              Text(this.videoImportResult)
                .fontSize(14).fontColor(this.videoImportResult.startsWith('OK') ? '#4a6cf7' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.videoImportResult.startsWith('OK') ? '#f0f4ff' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isVideoImporting) {
            LoadingProgress().width(36).height(36)
          }

          // ── 墨骨山河全集·8集视频（23.8分钟, 27.4MB）────────────
          Column() {
            Row() {
              Text('墨骨山河·全集视频')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 8集 23min ')
                .fontSize(11).fontColor('#27ae60')
                .backgroundColor('#e8f8f0')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('峄山碑前 → 永和九年那场雨 → 黄州突围 → 书谱之道 → 颠张醉素 → 安史之乱 → 碑学中兴 → 说文解字')
              .fontSize(11).fontColor('#888').margin({ top: 4 })
            Text('墨骨山河_ep01~ep08（李斯/王羲之/苏轼/孙过庭/张旭怀素/颜真卿/阮元/许慎）')
              .fontSize(10).fontColor('#27ae60').margin({ top: 2 })

            Column() {
              Text('一键导入全部')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入墨骨山河全集')
                .fontSize(14).backgroundColor('#27ae60').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doFullSeriesImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#f0fff8').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.fullSeriesImportResult.length > 0) {
            Column() {
              Text(this.fullSeriesImportResult)
                .fontSize(14).fontColor(this.fullSeriesImportResult.startsWith('OK') ? '#27ae60' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.fullSeriesImportResult.startsWith('OK') ? '#f0fff8' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isFullSeriesImporting) {
            LoadingProgress().width(36).height(36)
          }

          // ── 墨骨山河书法史卡包（8集 × 17张卡片）────────────────
          Column() {
            Row() {
              Text('墨骨山河·书法史系列')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 17张 ')
                .fontSize(11).fontColor('#e67e22')
                .backgroundColor('#fff3e0')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('配套视频包导入后可用；导入此卡包解锁链和视频条')
              .fontSize(12).fontColor('#888').margin({ top: 4 })

            Column() {
              Text('一键导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入墨骨山河')
                .fontSize(14).backgroundColor('#e67e22').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doMoguImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#fffbf0').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.moguImportResult.length > 0) {
            Column() {
              Text(this.moguImportResult)
                .fontSize(14).fontColor(this.moguImportResult.startsWith('OK') ? '#e67e22' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.moguImportResult.startsWith('OK') ? '#fffbf0' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isMoguImporting) {
            LoadingProgress().width(36).height(36)
          }

          Divider().color('#f0f0f0').margin({ top: 4, bottom: 4 })

          // ── 高考古诗文通关·完整版（gaokao v1）────────────────
          Column() {
            Row() {
              Text('高考古诗文通关·完整版')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 12集 ')
                .fontSize(11).fontColor('#9b59b6')
                .backgroundColor('#f5f0ff')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('41 条知识链 / 106 张文言文卡 / 18 张诗词卡 / 12 集')
              .fontSize(12).fontColor('#888').margin({ top: 4 })
            Text('含：判断句/使动意动/虚词系统/通假古今异义/被动句式/翻译采分点/推断六陷阱/意象五大群/比较鉴赏')
              .fontSize(11).fontColor('#9b59b6').margin({ top: 2 })

            Column() {
              Text('一键导入全部')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入高考古诗文')
                .fontSize(14).backgroundColor('#9b59b6').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doGaokaoImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#faf5ff').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.gaokaoImportResult.length > 0) {
            Column() {
              Text(this.gaokaoImportResult)
                .fontSize(14).fontColor(this.gaokaoImportResult.startsWith('OK') ? '#9b59b6' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.gaokaoImportResult.startsWith('OK') ? '#faf5ff' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isGaokaoImporting) {
            LoadingProgress().width(36).height(36)
          }

          Divider().color('#f0f0f0').margin({ top: 4, bottom: 4 })

          // ── 历史 v3 卡片包区块 ──────────────────────────────
          Column() {
            Row() {
              Text('历史 v3 卡片包')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 内置资源 ')
                .fontSize(11).fontColor('#5B8C5A')
                .backgroundColor('#f0fdf4')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('129 张卡片 / 16 条知识链')
              .fontSize(12).fontColor('#888').margin({ top: 4 })

            Column() {
              Text('一键导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('开始导入')
                .fontSize(14).backgroundColor('#5B8C5A').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doCardImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#f0fdf4').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.importResult.length > 0) {
            Column() {
              Text(this.importResult)
                .fontSize(14)
                .fontColor(this.importResult.startsWith('OK') ? '#5B8C5A' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.importResult.startsWith('OK') ? '#f0fdf4' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isImporting) {
            LoadingProgress().width(36).height(36)
          }

          // ── 国美书法校考·墨骨山河卡片包（cafa_calligraphy_2026）─────────
          Divider().color('#f0f0f0').margin({ top: 4, bottom: 4 })

          Column() {
            Row() {
              Text('国美书法校考·墨骨山河')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 18张 ')
                .fontSize(11).fontColor('#c0392b')
                .backgroundColor('#fff0f0')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('18 张考点卡片 / 9 条知识链（说文解字·六书·宋四家·译篆·句读）')
              .fontSize(12).fontColor('#888').margin({ top: 4 })
            Text('配套墨骨山河微剧本叙事，书法史 × 古汉语双模块覆盖')
              .fontSize(11).fontColor('#c0392b').margin({ top: 2 })

            Column() {
              Text('一键导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入书法校考')
                .fontSize(14).backgroundColor('#c0392b').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doCafaImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#fff5f5').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.cafaImportResult.length > 0) {
            Column() {
              Text(this.cafaImportResult)
                .fontSize(14)
                .fontColor(this.cafaImportResult.startsWith('OK') ? '#c0392b' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.cafaImportResult.startsWith('OK') ? '#fff5f5' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isCafaImporting) {
            LoadingProgress().width(36).height(36)
          }

          // ── 历史 v3 卡片包（更新：独立区块）────────────────────────
          Divider().color('#f0f0f0').margin({ top: 4, bottom: 4 })

          Column() {
            Row() {
              Text('历史 v3·共和新生')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' 129张 ')
                .fontSize(11).fontColor('#4a6cf7')
                .backgroundColor('#f0f4ff')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('近代史·共和新生系列：16 条知识链（鸦片战争→民国建立）')
              .fontSize(12).fontColor('#888').margin({ top: 4 })

            Column() {
              Text('一键导入')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入历史 v3')
                .fontSize(14).backgroundColor('#4a6cf7').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doHistoryV3Import())
            }
            .width('100%').padding(16)
            .backgroundColor('#f0f4ff').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.historyV3ImportResult.length > 0) {
            Column() {
              Text(this.historyV3ImportResult)
                .fontSize(14)
                .fontColor(this.historyV3ImportResult.startsWith('OK') ? '#4a6cf7' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.historyV3ImportResult.startsWith('OK') ? '#f0f4ff' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isHistoryV3Importing) {
            LoadingProgress().width(36).height(36)
          }

          // ── /data/local/tmp/ 临时导入（hdc push，spdt-content-cards 流）──
          Column() {
            Row() {
              Text('临时导入（hdc push 路径）')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
              Text(' /data/local/tmp/ ')
                .fontSize(11).fontColor('#e67e22')
                .backgroundColor('#fff3e0')
                .borderRadius(8).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .margin({ left: 8 })
            }.width('100%').alignItems(VerticalAlign.Center)

            Text('从 PC 推送的 rujing_cards.json（hdc file send 推到 /data/local/tmp/rujing_cards.json）')
              .fontSize(12).fontColor('#888').margin({ top: 4 })

            Column() {
              Text('读 /data/local/tmp/ 临时文件')
                .fontSize(16).fontWeight(600).fontColor('#1a1a1a')
                .alignSelf(ItemAlign.Start).margin({ bottom: 8 })
              Button('导入临时 JSON')
                .fontSize(14).backgroundColor('#e67e22').borderRadius(24)
                .width('80%').height(44)
                .onClick(() => this.doTempImport())
            }
            .width('100%').padding(16)
            .backgroundColor('#fff3e0').borderRadius(10)
            .margin({ top: 12 })
          }
          .width('100%').padding(20)
          .backgroundColor(Color.White).borderRadius(14)

          if (this.tempImportResult.length > 0) {
            Column() {
              Text(this.tempImportResult)
                .fontSize(14)
                .fontColor(this.tempImportResult.startsWith('OK') ? '#e67e22' : '#c0392b')
                .textAlign(TextAlign.Start).width('100%')
            }
            .width('100%').padding(16)
            .backgroundColor(this.tempImportResult.startsWith('OK') ? '#fff3e0' : '#fff5f5')
            .borderRadius(10)
          }

          if (this.isTempImporting) {
            LoadingProgress().width(36).height(36)
          }

          if (this.importedCards > 0 || this.importedVideos > 0 || this.fullSeriesVideos > 0) {
            Button('返回首页')
              .backgroundColor('#5B8C5A').borderRadius(24)
              .width('60%').margin({ top: 8 })
              .onClick(() => {
                router.clear();
                router.pushUrl({ url: 'pages/Index' });
              })
          }
        }
        .padding(20)
      }
      .layoutWeight(1).scrollBar(BarState.Off)
    }
    .width('100%').height('100%')
    .backgroundColor('#F5F5F5')
  }

  // ── 视频包导入（IF-B v2，内置 rawfile 模式）────────────────────
  // 流程：读 rawfile metadata.json → 复制 MP4 到沙箱 filesDir → 更新 video_file 路径 → 持久化
  // 资源文件：entry/src/main/resources/rawfile/ep01_metadata.json + ep01_pipeline.mp4

  async doVideoImport(): Promise<void> {
    this.isVideoImporting = true;
    this.videoImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;

    try {
      // Step 1：读取内置 metadata rawfile（ep06：秦+李斯书同文，对应墨骨山河_ep06）
      let metaText: string = '';
      try {
        const rawData: Uint8Array = await rm.getRawFileContent('ep06_metadata.json');
        const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });
        metaText = decoder.decodeToString(rawData);
      } catch (_) {
        this.videoImportResult = 'FAIL: 未找到 ep06_metadata.json（rawfile 资源缺失）';
        this.isVideoImporting = false;
        return;
      }

      // Step 2：解析 metadata
      let meta: Record<string, Object> = {};
      try {
        meta = JSON.parse(metaText) as Record<string, Object>;
      } catch (_) {
        this.videoImportResult = 'FAIL: metadata 解析失败';
        this.isVideoImporting = false;
        return;
      }

      const episodes = meta['episodes'] as Array<Record<string, Object>> | undefined;
      if (!episodes || episodes.length === 0) {
        this.videoImportResult = 'FAIL: episodes 为空';
        this.isVideoImporting = false;
        return;
      }

      // Step 3：从 rawfile 复制视频到应用沙箱
      const videoDir = getVideoDir();
      // 确保目录存在（防御性）
      try { fileIo.mkdirSync(videoDir, true); } catch (_) {}
      let copiedCount = 0;
      for (const ep of episodes) {
        const videoFile = ep['video_file'] as string;
        if (videoFile) {
          const dstPath = videoDir + videoFile;
          try {
            // 检查是否已复制（避免重复）
            if (fileIo.listFileSync(videoDir).includes(videoFile)) {
              console.info('[ImportPage] 视频已存在，跳过: ' + dstPath);
            } else {
              // 从 rawfile 读取二进制，写入沙箱
              const rawData: Uint8Array = await rm.getRawFileContent('ep01_pipeline.mp4');
              const fd: number = fileIo.openSync(dstPath,
                fileIo.OpenMode.CREATE | fileIo.OpenMode.WRITE_ONLY).fd;
              fileIo.writeSync(fd, rawData.buffer as ArrayBuffer);
              fileIo.closeSync(fd);
              console.info('[ImportPage] 视频复制完成: ' + dstPath);
            }
            // 更新 video_file 为沙箱绝对路径
            ep['video_file'] = dstPath;
            copiedCount++;
          } catch (e) {
            const err = e as BusinessError;
            console.error('[ImportPage] 视频复制失败 code=' + err.code + ' msg=' + err.message + ' dst=' + dstPath);
          }
        }
      }

      // Step 4：持久化 metadata（使用已更新 video_file 路径的 meta 对象）
      const updatedMetaJson = JSON.stringify(meta);
      const result = await importVideoPackage(updatedMetaJson);
      this.importedVideos = result.episodes;

      // 验证：读回 metadata 确认 video_file 路径已正确保存
      const savedMeta = getVideoMeta(result.package_id || '墨骨山河_EP06');
      if (savedMeta && savedMeta.episodes && savedMeta.episodes.length > 0) {
        const savedPath = savedMeta.episodes[0].video_file || '(empty)';
        this.videoImportResult = 'OK: ' + result.package_id + ' | ' + result.series_title +
          ' | ' + result.episodes.toString() + ' 集 | video_path=' + savedPath;
        promptAction.showToast({ message: '视频已导入，路径: ' + savedPath, duration: 3000 });
      } else {
        this.videoImportResult = 'FAIL: 视频路径未保存，savedMeta=' + JSON.stringify(savedMeta);
      }
    } catch (e) {
      this.videoImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isVideoImporting = false;
    }
  }

  // ── 墨骨山河卡包导入────────────────────────────────
  async doMoguImport(): Promise<void> {
    this.isMoguImporting = true;
    this.moguImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;
    try {
      const rawData: Uint8Array = await rm.getRawFileContent('mogustory_cards.json');
      const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });
      const text: string = decoder.decodeToString(rawData);
      const result = await importCardPackage(text);
      this.moguCards = result.cards;
      // 同时导入链叙事文本
      try {
        const narrData: Uint8Array = await rm.getRawFileContent('chain_narratives.json');
        const narrText: string = decoder.decodeToString(narrData);
        const chainCount: number = await importChainMeta(narrText);
        this.moguImportResult = 'OK: ' + result.cards.toString() + ' 张卡片 | ' + result.chains.toString() + ' 条链 | ' + chainCount.toString() + ' 叙事文本';
      } catch (_) {
        this.moguImportResult = 'OK: ' + result.cards.toString() + ' 张卡片 | ' + result.chains.toString() + ' 条链（无叙事）';
      }
    } catch (e) {
      this.moguImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isMoguImporting = false;
    }
  }

  // ── 高考古诗文通关导入（gaokao v1）────────────────
  async doGaokaoImport(): Promise<void> {
    this.isGaokaoImporting = true;
    this.gaokaoImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;
    const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });

    try {
      // Step 1：导入文言文卡包（gaokao_guwen_cards.json）
      let guwenCards = 0;
      let guwenChains = 0;
      try {
        const rawGuwen: Uint8Array = await rm.getRawFileContent('gaokao_guwen_cards.json');
        const textGuwen: string = decoder.decodeToString(rawGuwen);
        const resultGuwen = await importCardPackage(textGuwen);
        guwenCards = resultGuwen.cards;
        guwenChains = resultGuwen.chains;
      } catch (e) {
        this.gaokaoImportResult = 'FAIL: gaokao_guwen_cards.json 读取失败: ' + JSON.stringify(e);
        this.isGaokaoImporting = false;
        return;
      }

      // Step 2：导入古诗词卡包（gaokao_poetry_cards.json）
      let poetryCards = 0;
      try {
        const rawPoetry: Uint8Array = await rm.getRawFileContent('gaokao_poetry_cards.json');
        const textPoetry: string = decoder.decodeToString(rawPoetry);
        const resultPoetry = await importCardPackage(textPoetry);
        poetryCards = resultPoetry.cards;
      } catch (e) {
        // 古诗词文件不存在不影响主流程
        console.warn('[ImportPage] gaokao_poetry_cards.json 读取失败: ' + JSON.stringify(e));
      }

      // Step 3：导入知识链叙事（gaokao_chain_narratives.json）
      let chainNarratives = 0;
      try {
        const rawNarr: Uint8Array = await rm.getRawFileContent('gaokao_chain_narratives.json');
        const textNarr: string = decoder.decodeToString(rawNarr);
        chainNarratives = await importChainMeta(textNarr);
      } catch (e) {
        console.warn('[ImportPage] gaokao_chain_narratives.json 读取失败: ' + JSON.stringify(e));
      }

      // Step 4：读 metadata 并打印汇总
      let metaInfo = '';
      try {
        const rawMeta: Uint8Array = await rm.getRawFileContent('gaokao_metadata.json');
        const textMeta: string = decoder.decodeToString(rawMeta);
        const meta = JSON.parse(textMeta) as Record<string, Object>;
        metaInfo = ' | 12集 | ' + (meta['total_episodes'] || '?') + ' episodes';
      } catch (_) {
        // metadata 缺失不影响主流程
      }

      const totalCards = guwenCards + poetryCards;
      this.gaokaoCards = totalCards;
      this.gaokaoChains = guwenChains;
      this.gaokaoImportResult = 'OK: ' + totalCards.toString() + ' 张卡片（' +
        guwenCards.toString() + ' 文言+' + poetryCards.toString() + ' 诗词）| ' +
        guwenChains.toString() + ' 链 | ' + chainNarratives.toString() + ' 叙事' + metaInfo;

      promptAction.showToast({
        message: '高考古诗文 ' + totalCards.toString() + ' 张卡片已导入',
        duration: 3000
      });
    } catch (e) {
      this.gaokaoImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isGaokaoImporting = false;
    }
  }

  // ── 卡片包导入（原有逻辑）─────────────────────────────

  async doCardImport(): Promise<void> {
    this.isImporting = true;
    this.importResult = '读取中...';

    try {
      const ctx = getContext(this);
      const rm = ctx.resourceManager;
      const rawData: Uint8Array = await rm.getRawFileContent('rujing_cards.json');
      const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });
      const text: string = decoder.decodeToString(rawData);

      const result = await importCardPackage(text);
      this.importedCards += result.cards;
      this.importedChains += result.chains;

      // 同时导入链叙事文本
      try {
        const narrData: Uint8Array = await rm.getRawFileContent('chain_narratives.json');
        const narrText: string = decoder.decodeToString(narrData);
        const chainCount: number = await importChainMeta(narrText);
        this.importResult = 'OK: ' + result.cards.toString() + ' cards, ' + result.chains.toString() + ' chains, ' + chainCount.toString() + ' narratives';
      } catch (_) {
        this.importResult = 'OK: ' + result.cards.toString() + ' cards, ' + result.chains.toString() + ' chains (no narratives)';
      }
    } catch (e) {
      this.importResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isImporting = false;
    }
  }

  // ── 国美书法校考·墨骨山河卡片包导入─────────────────────
  // 源：cafa_calligraphy_2026/kb_vocab.json → cafa_cards.json（18张/9链）
  // 叙事：cafa_chain_narratives.json

  async doCafaImport(): Promise<void> {
    this.isCafaImporting = true;
    this.cafaImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;
    const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });

    try {
      // Step 1：导入卡片包
      const rawCards: Uint8Array = await rm.getRawFileContent('cafa_cards.json');
      const textCards: string = decoder.decodeToString(rawCards);
      const resultCards = await importCardPackage(textCards);
      this.cafaCards = resultCards.cards;
      this.cafaChains = resultCards.chains;

      // Step 2：导入链叙事文本
      let chainNarratives = 0;
      try {
        const rawNarr: Uint8Array = await rm.getRawFileContent('cafa_chain_narratives.json');
        const textNarr: string = decoder.decodeToString(rawNarr);
        chainNarratives = await importChainMeta(textNarr);
      } catch (e) {
        console.warn('[ImportPage] cafa_chain_narratives.json 读取失败: ' + JSON.stringify(e));
      }

      this.cafaImportResult = 'OK: ' + resultCards.cards.toString() + ' 张卡片 | ' +
        resultCards.chains.toString() + ' 条链 | ' + chainNarratives.toString() + ' 叙事文本 | 书法×古汉语双模块';

      promptAction.showToast({
        message: '书法校考 ' + resultCards.cards.toString() + ' 张卡片已导入',
        duration: 3000
      });
    } catch (e) {
      this.cafaImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isCafaImporting = false;
    }
  }

  // ── 历史 v3 卡片包导入（独立区块）────────────────────
  // 源：PT-038 古史_v3_全16链卡片包.json → history_v3_cards.json（129张/16链）

  async doHistoryV3Import(): Promise<void> {
    this.isHistoryV3Importing = true;
    this.historyV3ImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;
    const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });

    try {
      const rawData: Uint8Array = await rm.getRawFileContent('history_v3_cards.json');
      const text: string = decoder.decodeToString(rawData);
      const result = await importCardPackage(text);
      this.historyV3Cards = result.cards;
      this.historyV3ImportResult = 'OK: ' + result.cards.toString() + ' 张卡片 | ' +
        result.chains.toString() + ' 条链 | 近代史·共和新生系列';

      promptAction.showToast({
        message: '历史 v3 ' + result.cards.toString() + ' 张卡片已导入',
        duration: 3000
      });
    } catch (e) {
      this.historyV3ImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isHistoryV3Importing = false;
    }
  }

  // v2.1: /data/local/tmp/ 临时导入（hdc push 路径，spdt-content-cards 流）
  // 流程：fileIo.openSync 读 /data/local/tmp/rujing_cards.json → 解析 → 调 importCardPackage
  async doTempImport(): Promise<void> {
    this.isTempImporting = true;
    this.tempImportResult = '读取中...';
    const tmpPath = '/data/local/tmp/rujing_cards.json';
    try {
      const file = fileIo.openSync(tmpPath, fileIo.OpenMode.READ_ONLY);
      const stat = fileIo.statSync(tmpPath);
      const buf: ArrayBuffer = new ArrayBuffer(stat.size);
      fileIo.readSync(file.fd, buf);
      fileIo.closeSync(file);
      const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });
      const text: string = decoder.decodeToString(new Uint8Array(buf));

      const result = await importCardPackage(text);
      this.tempImportedCards = result.cards;
      this.tempImportedChains = result.chains;
      this.tempImportResult = 'OK: ' + result.cards.toString() + ' 张卡片 | ' +
        result.chains.toString() + ' 条链 | 来自 ' + tmpPath + ' | ' + text.length.toString() + ' 字符';

      promptAction.showToast({
        message: '临时 JSON ' + result.cards.toString() + ' 张卡片已导入',
        duration: 3000
      });
    } catch (e) {
      this.tempImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isTempImporting = false;
    }
  }

  // ── 墨骨山河全集·8集视频导入────────────────────────────────
  // 源：墨骨山河全集_metadata.json（8集汇总）+ 墨骨山河_ep01~ep08.mp4

  async doFullSeriesImport(): Promise<void> {
    this.isFullSeriesImporting = true;
    this.fullSeriesImportResult = '';
    const ctx = getContext(this);
    const rm = ctx.resourceManager;

    try {
      // Step 1：读取汇总 metadata
      const rawMeta: Uint8Array = await rm.getRawFileContent('墨骨山河全集_metadata.json');
      const decoder: util.TextDecoder = util.TextDecoder.create('utf-8', { ignoreBOM: true });
      const metaText: string = decoder.decodeToString(rawMeta);
      const meta = JSON.parse(metaText) as Record<string, Object>;

      const episodes = meta['episodes'] as Array<Record<string, Object>> | undefined;
      if (!episodes || episodes.length === 0) {
        this.fullSeriesImportResult = 'FAIL: episodes 为空';
        this.isFullSeriesImporting = false;
        return;
      }

      // Step 2：复制每个视频到应用沙箱，并更新 video_file 路径
      const videoDir = getVideoDir();
      try { fileIo.mkdirSync(videoDir, true); } catch (_) {}
      let copiedCount = 0;
      let totalDuration = 0;

      for (const ep of episodes) {
        const videoFile = ep['video_file'] as string;
        const epNum = ep['ep'] as number;
        const epTitle = (ep['title'] as string) || ('ep' + epNum);
        const duration = (ep['duration_seconds'] as number) || 0;
        totalDuration += duration;

        if (!videoFile) continue;
        const dstPath = videoDir + videoFile;

        try {
          if (fileIo.listFileSync(videoDir).includes(videoFile)) {
            console.info('[FullSeries] 视频已存在，跳过: ' + dstPath);
          } else {
            // 从 rawfile 读取并写入沙箱
            const rawData: Uint8Array = await rm.getRawFileContent(videoFile);
            const fd: number = fileIo.openSync(dstPath,
              fileIo.OpenMode.CREATE | fileIo.OpenMode.WRITE_ONLY).fd;
            fileIo.writeSync(fd, rawData.buffer as ArrayBuffer);
            fileIo.closeSync(fd);
            console.info('[FullSeries] 视频复制: ' + videoFile);
          }
          // 更新 metadata 中的路径为绝对路径
          ep['video_file'] = dstPath;
          copiedCount++;
        } catch (e) {
          const err = e as BusinessError;
          console.error('[FullSeries] 复制失败 ep' + epNum + ': ' + err.code + ' ' + err.message);
        }
      }

      // Step 3：持久化汇总 metadata
      const updatedMetaJson: string = JSON.stringify(meta);
      const result = await importVideoPackage(updatedMetaJson);
      this.fullSeriesVideos = result.episodes ?? copiedCount;

      // 计算总时长
      const min = Math.floor(totalDuration / 60);
      const sec = Math.round(totalDuration % 60);
      this.fullSeriesDuration = min + '分' + sec + '秒';

      this.fullSeriesImportResult = 'OK: ' + (result.episodes ?? copiedCount).toString() +
        ' 集 | ' + this.fullSeriesDuration + ' | ' +
        episodes.length.toString() + ' 个视频文件已就位';

      promptAction.showToast({
        message: '墨骨山河全集 ' + this.fullSeriesVideos.toString() + ' 集已导入',
        duration: 3000
      });
    } catch (e) {
      this.fullSeriesImportResult = 'FAIL: ' + JSON.stringify(e);
    } finally {
      this.isFullSeriesImporting = false;
    }
  }
}
