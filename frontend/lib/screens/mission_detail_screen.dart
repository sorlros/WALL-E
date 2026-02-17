import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/mission_model.dart';
import '../models/detection_model.dart';

class MissionDetailScreen extends StatelessWidget {
  final Mission mission;

  const MissionDetailScreen({super.key, required this.mission});

  @override
  Widget build(BuildContext context) {
    final detections = mission.detections;

    return Scaffold(
      backgroundColor: const Color(0xFF101622),
      appBar: AppBar(
        title: Text(mission.name),
        backgroundColor: const Color(0xFF101622),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mission Info
            _buildInfoCard(),
            const SizedBox(height: 24),

            // Detections Grid Header
            Text(
              '감지된 결합 (${detections.length})',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            // Detections Grid
            detections.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32.0),
                      child: Text(
                        '감지된 결함이 없습니다.',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ),
                  )
                : GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          crossAxisSpacing: 12,
                          mainAxisSpacing: 12,
                          childAspectRatio: 0.8,
                        ),
                    itemCount: detections.length,
                    itemBuilder: (context, index) {
                      final detection = detections[index];
                      return _buildDetectionCard(context, detection);
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A2332),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '미션 설명',
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            mission.description ?? '설명 없음',
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
          const SizedBox(height: 12),
          Text(
            '발생 일시',
            style: const TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            mission.createdAt.toIso8601String().split('T')[0],
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildDetectionCard(BuildContext context, Detection detection) {
    // Construct full image URL
    // image_url is like: "/storage/images/2024-xx-xx/uuid.jpg"
    final imageUrl = '${ApiService.baseUrl}${detection.imageUrl}';

    return GestureDetector(
      onTap: () {
        // TODO: Show full screen image
        showDialog(
          context: context,
          builder: (context) => Dialog(
            backgroundColor: Colors.transparent,
            child: InteractiveViewer(child: Image.network(imageUrl)),
          ),
        );
      },
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1A2332),
          borderRadius: BorderRadius.circular(12),
          image: DecorationImage(
            image: NetworkImage(imageUrl),
            fit: BoxFit.cover,
          ),
        ),
        child: Stack(
          children: [
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: const BorderRadius.vertical(
                    bottom: Radius.circular(12),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      detection.label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      '${(detection.confidence * 100).toStringAsFixed(1)}%',
                      style: TextStyle(
                        color: (detection.confidence > 0.8)
                            ? Colors.red
                            : Colors.orange,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
