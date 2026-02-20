import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/mission_model.dart';
import '../models/detection_model.dart';

class MissionDetailScreen extends StatefulWidget {
  final Mission mission;

  const MissionDetailScreen({super.key, required this.mission});

  @override
  State<MissionDetailScreen> createState() => _MissionDetailScreenState();
}

class _MissionDetailScreenState extends State<MissionDetailScreen> {
  late Mission mission;
  bool isLoading = false;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    mission = widget.mission;
    // _fetchMissionDetails();
  }

  /*
  Future<void> _fetchMissionDetails() async {
    setState(() {
      isLoading = true;
    });
    try {
      final updatedMission = await ApiService.getMission(widget.mission.id);
      if (mounted) {
        setState(() {
          mission = updatedMission;
          isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          errorMessage = e.toString();
          isLoading = false;
        });
      }
    }
  }
  */

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Scaffold(
        backgroundColor: Color(0xFF101622),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (errorMessage != null) {
      return Scaffold(
        backgroundColor: const Color(0xFF101622),
        appBar: AppBar(
          title: const Text('미션 상세'),
          backgroundColor: const Color(0xFF101622),
        ),
        body: Center(
          child: Text(errorMessage!, style: const TextStyle(color: Colors.red)),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF101622),
      appBar: AppBar(
        title: const Text('미션 상세'),
        backgroundColor: const Color(0xFF101622),
        elevation: 0,
      ),
      body: OrientationBuilder(
        builder: (context, orientation) {
          return orientation == Orientation.portrait
              ? _buildPortraitLayout()
              : _buildLandscapeLayout();
        },
      ),
    );
  }

  Widget _buildPortraitLayout() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildInfoCard(),
          const SizedBox(height: 24),
          _buildGridHeader(),
          const SizedBox(height: 12),
          _buildDetectionsGrid(),
        ],
      ),
    );
  }

  Widget _buildLandscapeLayout() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Left: Info Card (Scrollable if needed)
        Expanded(
          flex: 2,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(children: [_buildInfoCard()]),
          ),
        ),
        // Right: Grid (Scrollable)
        Expanded(
          flex: 3,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.only(
                  top: 16.0,
                  right: 16.0,
                  left: 8.0,
                ),
                child: _buildGridHeader(),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(
                    right: 16.0,
                    bottom: 16.0,
                    left: 8.0,
                  ),
                  child: _buildDetectionsGrid(crossAxisCount: 3),
                ),
              ),
            ],
          ),
        ),
      ],
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
          const Text(
            '미션 설명',
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            mission.description ?? '설명 없음',
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
          const SizedBox(height: 12),
          const Text(
            '발생 일시',
            style: TextStyle(color: Colors.grey, fontSize: 12),
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

  Widget _buildGridHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          '감지된 결함 (${mission.detections.length})',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildDetectionsGrid({int crossAxisCount = 2}) {
    final detections = mission.detections;
    return detections.isEmpty
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
            physics: const ClampingScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: crossAxisCount,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.8,
            ),
            itemCount: detections.length,
            itemBuilder: (context, index) {
              final detection = detections[index];
              return _buildDetectionCard(context, detection, detections);
            },
          );
  }

  Widget _buildDetectionCard(
    BuildContext context,
    Detection detection,
    List<Detection> allDetections,
  ) {
    final imageUrl = '${ApiService.baseUrl}${detection.imageUrl}';

    return GestureDetector(
      onTap: () {
        final index = allDetections.indexOf(detection);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => DetectionFullScreenView(
              detections: allDetections,
              initialIndex: index,
            ),
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
                        color: (detection.confidence > 0.7)
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

class DetectionFullScreenView extends StatefulWidget {
  final List<Detection> detections;
  final int initialIndex;

  const DetectionFullScreenView({
    super.key,
    required this.detections,
    required this.initialIndex,
  });

  @override
  State<DetectionFullScreenView> createState() =>
      _DetectionFullScreenViewState();
}

class _DetectionFullScreenViewState extends State<DetectionFullScreenView> {
  late PageController _pageController;
  late int _currentIndex;
  bool _showBox = true;
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final currentDetection = widget.detections[_currentIndex];

    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: () {
          setState(() {
            _showControls = !_showControls;
          });
        },
        child: Stack(
          children: [
            PageView.builder(
              controller: _pageController,
              itemCount: widget.detections.length,
              onPageChanged: (index) {
                setState(() {
                  _currentIndex = index;
                });
              },
              itemBuilder: (context, index) {
                final detection = widget.detections[index];
                final imageUrl = '${ApiService.baseUrl}${detection.imageUrl}';
                return _DetectionImagePage(
                  detection: detection,
                  imageUrl: imageUrl,
                  showBox: _showBox,
                );
              },
            ),

            AnimatedOpacity(
              opacity: _showControls ? 1.0 : 0.0,
              duration: const Duration(milliseconds: 200),
              child: Container(
                height: kToolbarHeight + MediaQuery.of(context).padding.top,
                padding: EdgeInsets.only(
                  top: MediaQuery.of(context).padding.top,
                  left: 8,
                  right: 16,
                ),
                color: Colors.black.withOpacity(0.5),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.white),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            currentDetection.label,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          Text(
                            '${_currentIndex + 1} / ${widget.detections.length}',
                            style: const TextStyle(
                              color: Colors.grey,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Row(
                      children: [
                        const Text(
                          'AI Box',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const SizedBox(width: 8),
                        Switch(
                          value: _showBox,
                          activeThumbColor: Colors.green,
                          onChanged: (value) {
                            setState(() {
                              _showBox = value;
                            });
                          },
                        ),
                      ],
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

class _DetectionImagePage extends StatefulWidget {
  final Detection detection;
  final String imageUrl;
  final bool showBox;

  const _DetectionImagePage({
    required this.detection,
    required this.imageUrl,
    required this.showBox,
  });

  @override
  State<_DetectionImagePage> createState() => _DetectionImagePageState();
}

class _DetectionImagePageState extends State<_DetectionImagePage> {
  Size? _imageSize;

  @override
  void initState() {
    super.initState();
    _resolveImageSize();
  }

  @override
  void didUpdateWidget(covariant _DetectionImagePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.imageUrl != widget.imageUrl) {
      _resolveImageSize();
    }
  }

  void _resolveImageSize() {
    final ImageStream stream = NetworkImage(
      widget.imageUrl,
    ).resolve(ImageConfiguration.empty);
    stream.addListener(
      ImageStreamListener((ImageInfo info, bool synchronousCall) {
        if (mounted) {
          setState(() {
            _imageSize = Size(
              info.image.width.toDouble(),
              info.image.height.toDouble(),
            );
          });
        }
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: InteractiveViewer(
        minScale: 0.5,
        maxScale: 4.0,
        boundaryMargin: const EdgeInsets.all(double.infinity),
        child: LayoutBuilder(
          builder: (context, constraints) {
            Size displaySize = Size.zero;

            if (_imageSize != null) {
              double aspectRatio = _imageSize!.width / _imageSize!.height;
              double containerAspectRatio =
                  constraints.maxWidth / constraints.maxHeight;

              if (aspectRatio > containerAspectRatio) {
                displaySize = Size(
                  constraints.maxWidth,
                  constraints.maxWidth / aspectRatio,
                );
              } else {
                displaySize = Size(
                  constraints.maxHeight * aspectRatio,
                  constraints.maxHeight,
                );
              }
            } else {
              displaySize = Size(constraints.maxWidth, constraints.maxHeight);
            }

            return Stack(
              alignment: Alignment.center,
              clipBehavior: Clip.none,
              children: [
                Image.network(
                  widget.imageUrl,
                  fit: BoxFit.contain,
                  width: double.infinity,
                  height: double.infinity,
                  loadingBuilder: (context, child, progress) {
                    if (progress == null) return child;
                    return const Center(child: CircularProgressIndicator());
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return const Center(
                      child: Text(
                        'Error loading image',
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  },
                ),
                if (widget.showBox &&
                    widget.detection.bbox != null &&
                    _imageSize != null)
                  SizedBox(
                    width: displaySize.width,
                    height: displaySize.height,
                    child: CustomPaint(
                      painter: _DetectionPainter(
                        bbox: widget.detection.bbox!,
                        label: widget.detection.label,
                        confidence: widget.detection.confidence,
                      ),
                    ),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _DetectionPainter extends CustomPainter {
  final List<dynamic> bbox;
  final String label;
  final double confidence;

  _DetectionPainter({
    required this.bbox,
    required this.label,
    required this.confidence,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;

    final textStyle = const TextStyle(
      color: Colors.white,
      fontSize: 14,
      backgroundColor: Colors.red,
    );

    final double x = bbox[0];
    final double y = bbox[1];
    final double w = bbox[2];
    final double h = bbox[3];

    final double left = (x - w / 2) * size.width;
    final double top = (y - h / 2) * size.height;
    final double width = w * size.width;
    final double height = h * size.height;

    final rect = Rect.fromLTWH(left, top, width, height);
    canvas.drawRect(rect, paint);

    final labelText = '$label ${(confidence * 100).toInt()}%';
    final textSpan = TextSpan(text: labelText, style: textStyle);
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(left, top - 20));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return false;
  }
}
