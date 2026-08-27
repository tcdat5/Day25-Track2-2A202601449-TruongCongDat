# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## 1. Baseline vs. Optimized

Baseline là **$27,133/tháng**, optimized còn **$14,626/tháng**. NimbusAI tiết kiệm **$12,507/tháng**, tương đương **46.1%**.
Riêng inference giảm từ **$6.488** xuống **$1.126/1M-token**, giảm **82.6%**.

## 2. Phân tích từng đòn bẩy

Đòn bẩy đóng góp lớn nhất là **Purchasing (spot/reserved)**, tiết kiệm **$10,040/tháng**. Reserved phù hợp với workload chạy ổn định ở duty cycle cao, còn spot phù hợp với workload interruptible có checkpoint; cả hai đều giảm trực tiếp chi phí GPU-giờ.
Inference (cascade/cache/batch) tiết kiệm **$1,212** nhờ route phần lớn request sang model nhỏ, giảm giá input bằng cache và giảm thêm 50% cho batch.
Right-sizing tiết kiệm **$655** bằng cách hạ tier GPU có MFU thấp; tắt GPU idle tiết kiệm thêm **$600** mà không ảnh hưởng throughput.

## 3. GPU-Util Lie

M1 phát hiện **gpu-h100-4, gpu-a10g-1**. Các GPU này có GPU-Util ≥90% nhưng MFU <30%: clock vẫn hoạt động nhưng phần lớn thời gian có thể bị memory stall, kernel launch overhead hoặc chờ I/O, nên FLOPs hữu ích thấp.
Hậu quả là vẫn trả đủ GPU-hour cho hiệu suất thấp. Hạ tier các GPU bị lie ước tính tiết kiệm **$655/tháng**; idle waste hiện tại là **$600/tháng**. Vì vậy cần theo dõi MFU/MBU cùng GPU-Util.

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

## Extensions

### Reasoning budget

- Reasoning traffic: 8.4% of requests / 16.5% of tokens; optimized cost: 16.5%.
- A 10% traffic cap is estimated to save $0.00/day and 0 Wh/day. Current traffic is below the cap: 8.4% requests.
- Insight: reasoning uses disproportionately long outputs, so it consumes more tokens and energy; apply reasoning only when task complexity justifies it.
### Prompt cache economics

- Average reads: 2.0; write cost: $0.50/1M tokens.
- Cache enabled: **True** (break-even rule: repeated-read savings exceed write cost).
- Break-even: each read saves 90%; 2.0 reads save $1.80, greater than the $0.50 write cost.
### Inference unit economics

- Baseline: $6.488/1M tokens; optimized: $1.126/1M tokens (82.6% lower).

## 5. Khuyến nghị cho NimbusAI

1. **Chuẩn hóa purchasing ngay:** dùng reserved cho job ổn định, spot + checkpoint cho job interruptible; rà soát lại theo duty cycle hàng tháng.
2. **Thiết lập guardrail hiệu quả GPU:** dashboard MFU, MBU, idle hours và $/1M-token; tự động cảnh báo GPU-Util cao nhưng MFU thấp và tắt GPU idle.
3. **Tối ưu traffic có kiểm soát chất lượng:** cascade mặc định, prompt cache cho prefix lặp lại, batch cho request không yêu cầu realtime; chỉ bật reasoning khi cần và giữ tag coverage ≥80%.

_Figures are June-2026 as-of snapshots; re-baseline before acting._