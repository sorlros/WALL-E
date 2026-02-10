import 'package:flutter/material.dart';

class AnalysisReportScreen extends StatelessWidget {
  static const routeName = '/analysis-report';
  const AnalysisReportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Report'),
        leading: const BackButton(),
      ),
      body: Column(
        children: [
          Container(
            height: 200,
            width: double.infinity,
            color: Colors.grey[300],
            child: const Center(child: Text("Main Image View")),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Row(
                  children: const [
                    _CrackThumbnail(id: 'CRACK-01', severity: 'HIGH'),
                    SizedBox(width: 12),
                    _CrackThumbnail(id: 'CRACK-02', severity: 'MED'),
                  ],
                ),
                const SizedBox(height: 20),
                const _InfoCard(label: 'EST. WIDTH', value: '1.28 mm'),
                const _InfoCard(label: 'TYPE', value: 'VERTICAL'),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Marked False Positive')),
                      );
                    },
                    child: const Text('Mark False Positive'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      // Navigator.pushNamed(
                      //   context,
                      //   ExportReportScreen.routeName,
                      // );
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Export Feature (TODO)')),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Confirm Observation'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CrackThumbnail extends StatelessWidget {
  final String id;
  final String severity;
  const _CrackThumbnail({required this.id, required this.severity});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120,
      height: 120,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.orange),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Center(child: Text('$id\n$severity', textAlign: TextAlign.center)),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String label;
  final String value;
  const _InfoCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(label, style: const TextStyle(fontSize: 12)),
        subtitle: Text(
          value,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}
